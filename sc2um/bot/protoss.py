"""The sc2um Protoss bot: reads python-sc2 game state, applies sc2um.bot.plan."""

from __future__ import annotations

from sc2.bot_ai import BotAI
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

from sc2um.bot import plan

ARMY_TYPES = {UnitTypeId.ZEALOT, UnitTypeId.STALKER}
ARMY_UNIT_SUPPLY = 2
DEFEND_RADIUS = 20


class ProtossGatewayBot(BotAI):
    """One-base Protoss bot: Probes to saturation, Pylons by supply,
    Gateways, then attacks with Zealots and Stalkers at a supply threshold."""

    def __init__(self, config: plan.PlanConfig = plan.PlanConfig()) -> None:
        super().__init__()
        self.config = config
        self.attacking = False
        self.last_game_loop = 0
        self.game_result = None
        self._scout_index = 0

    # --- state -----------------------------------------------------------
    def army(self):
        return self.units.of_type(ARMY_TYPES)

    def enemies_near_base(self):
        if not self.structures:
            return self.enemy_units.none
        return self.enemy_units.filter(
            lambda e: not e.is_flying or e.can_attack_ground
        ).filter(lambda e: self.structures.closer_than(DEFEND_RADIUS, e.position).exists)

    def macro_state(self) -> plan.MacroState:
        nexuses = self.townhalls.ready
        gateways = self.structures(UnitTypeId.GATEWAY)
        core = self.structures(UnitTypeId.CYBERNETICSCORE)
        assimilators = self.structures(UnitTypeId.ASSIMILATOR)
        return plan.MacroState(
            minerals=int(self.minerals),
            vespene=int(self.vespene),
            supply_used=int(self.supply_used),
            supply_cap=int(self.supply_cap),
            workers=self.workers.amount,
            army_supply=ARMY_UNIT_SUPPLY * self.army().amount,
            nexus_count=max(nexuses.amount, 1),
            idle_nexuses=nexuses.idle.amount,
            pylons=self.structures(UnitTypeId.PYLON).ready.amount,
            pylons_pending=int(self.already_pending(UnitTypeId.PYLON)),
            gateways=gateways.ready.amount,
            gateways_pending=int(self.already_pending(UnitTypeId.GATEWAY)),
            idle_gateways=gateways.ready.idle.amount,
            assimilators=assimilators.ready.amount,
            assimilators_pending=int(self.already_pending(UnitTypeId.ASSIMILATOR)),
            cybernetics_core_ready=core.ready.exists,
            cybernetics_core_pending=bool(self.already_pending(UnitTypeId.CYBERNETICSCORE)),
            pending_probes=int(self.already_pending(UnitTypeId.PROBE)),
            enemies_near_base=self.enemies_near_base().amount,
            attacking=self.attacking,
        )

    # --- main loop -------------------------------------------------------
    async def on_step(self, iteration: int) -> None:
        self.last_game_loop = self.state.game_loop
        if not self.townhalls:
            # No Nexus left: send everything at the enemy.
            for unit in self.units:
                unit.attack(self.enemy_start_locations[0])
            return
        if iteration % 4 == 0:
            await self.distribute_workers()

        state = self.macro_state()
        actions = plan.decide(state, self.config)
        for action in actions:
            await self._do(action)

    async def _do(self, action: str) -> None:
        nexus = self.townhalls.ready.first if self.townhalls.ready else self.townhalls.first
        if action == plan.TRAIN_PROBE:
            idle = self.townhalls.ready.idle
            if idle:
                idle.first.train(UnitTypeId.PROBE)
        elif action == plan.BUILD_PYLON:
            near = nexus.position.towards_with_random_angle(self.game_info.map_center, distance=8)
            await self.build(UnitTypeId.PYLON, near=near, placement_step=3)
        elif action in (plan.BUILD_GATEWAY, plan.BUILD_CYBERNETICS_CORE):
            pylons = self.structures(UnitTypeId.PYLON).ready
            if pylons:
                kind = UnitTypeId.GATEWAY if action == plan.BUILD_GATEWAY else UnitTypeId.CYBERNETICSCORE
                await self.build(kind, near=pylons.random.position.towards(nexus.position, -3))
        elif action == plan.BUILD_ASSIMILATOR:
            taken = {a.position for a in self.structures(UnitTypeId.ASSIMILATOR)}
            for geyser in self.vespene_geyser.closer_than(12, nexus):
                if geyser.position in taken:
                    continue
                worker = self.select_build_worker(geyser.position)
                if worker:
                    worker.build_gas(geyser)
                break
        elif action in (plan.TRAIN_ZEALOT, plan.TRAIN_STALKER):
            kind = UnitTypeId.STALKER if action == plan.TRAIN_STALKER else UnitTypeId.ZEALOT
            idle = self.structures(UnitTypeId.GATEWAY).ready.idle
            if idle:
                idle.first.train(kind)
        elif action == plan.DEFEND:
            threats = self.enemies_near_base()
            for unit in self.army():
                if threats:
                    unit.attack(threats.closest_to(unit).position)
        elif action == plan.ATTACK:
            self.attacking = True
            target = self.attack_target()
            for unit in self.army():
                unit.attack(target)
        elif action == plan.RETREAT:
            self.attacking = False
            rally = nexus.position.towards(self.game_info.map_center, 8)
            for unit in self.army():
                unit.move(rally)

    def attack_target(self) -> Point2:
        """Closest known enemy structure, else the enemy start, else expansions."""
        army = self.army()
        origin = army.center if army else self.start_location
        if self.enemy_structures:
            return self.enemy_structures.closest_to(origin).position
        start = self.enemy_start_locations[0]
        if army and army.closer_than(7, start).amount < army.amount // 2:
            return start
        # Start location is cleared but the enemy is still alive: sweep bases.
        expansions = sorted(self.expansion_locations_list, key=lambda p: p.distance_to(start))
        if not expansions:
            return start
        target = expansions[self._scout_index % len(expansions)]
        if army and army.closer_than(7, target).exists:
            self._scout_index += 1
        return target

    async def on_end(self, game_result: Result) -> None:
        self.game_result = game_result
