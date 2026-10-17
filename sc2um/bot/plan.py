"""Macro plan for the sc2um Protoss bot, as pure functions.

This module has no dependency on python-sc2 or the game, so the
decisions can be unit-tested on plain values. ``sc2um.bot.protoss``
reads the game state into a :class:`MacroState`, asks :func:`decide`
what to do and carries the actions out.

The plan is deliberately simple:

1. Train Probes until the main base is saturated (16 on minerals plus
   3 per Assimilator).
2. Build a Pylon when supply is running low.
3. Build Gateways (and one Cybernetics Core and two Assimilators).
4. Train Zealots, and Stalkers once the Cybernetics Core is ready.
5. Attack with the whole gateway army once its supply reaches a
   threshold; fall back when it drops low, then rebuild and attack again.
"""

from __future__ import annotations

from dataclasses import dataclass

# Mineral / gas costs (StarCraft II 4.10 values).
COST = {
    "probe": (50, 0),
    "pylon": (100, 0),
    "gateway": (150, 0),
    "assimilator": (75, 0),
    "cybernetics_core": (150, 0),
    "zealot": (100, 0),
    "stalker": (125, 50),
}

MINERAL_WORKERS_PER_BASE = 16
WORKERS_PER_ASSIMILATOR = 3

# Action names returned by decide().
TRAIN_PROBE = "train_probe"
BUILD_PYLON = "build_pylon"
BUILD_GATEWAY = "build_gateway"
BUILD_ASSIMILATOR = "build_assimilator"
BUILD_CYBERNETICS_CORE = "build_cybernetics_core"
TRAIN_ZEALOT = "train_zealot"
TRAIN_STALKER = "train_stalker"
ATTACK = "attack"
RETREAT = "retreat"
DEFEND = "defend"


@dataclass(frozen=True)
class PlanConfig:
    max_gateways: int = 4
    max_assimilators: int = 2
    attack_supply: int = 20
    retreat_supply: int = 6
    first_gateway_supply: int = 14
    assimilator_supply: int = 16


@dataclass(frozen=True)
class MacroState:
    minerals: int
    vespene: int
    supply_used: int
    supply_cap: int
    workers: int
    army_supply: int
    nexus_count: int = 1
    idle_nexuses: int = 1
    pylons: int = 0
    pylons_pending: int = 0
    gateways: int = 0
    gateways_pending: int = 0
    idle_gateways: int = 0
    assimilators: int = 0
    assimilators_pending: int = 0
    cybernetics_core_ready: bool = False
    cybernetics_core_pending: bool = False
    pending_probes: int = 0
    enemies_near_base: int = 0
    attacking: bool = False

    @property
    def supply_left(self) -> int:
        return self.supply_cap - self.supply_used


def worker_target(state: MacroState) -> int:
    """Probes needed to saturate the bases and Assimilators we have."""
    gas = state.assimilators + state.assimilators_pending
    return state.nexus_count * MINERAL_WORKERS_PER_BASE + gas * WORKERS_PER_ASSIMILATOR


def pylon_needed(state: MacroState) -> bool:
    """Build a Pylon when the supply buffer is smaller than production can use."""
    if state.supply_cap >= 200:
        return False
    # Each Nexus and Gateway can add about 2 supply per cycle.
    buffer = 2 + 2 * (state.idle_nexuses + state.gateways)
    max_pending = 1 if state.supply_cap < 60 else 2
    return state.supply_left <= buffer and state.pylons_pending < max_pending


def next_attack_mode(state: MacroState, config: PlanConfig = PlanConfig()) -> bool:
    """Whether the army should be attacking, with hysteresis."""
    if state.attacking:
        return state.army_supply > config.retreat_supply
    return state.army_supply >= config.attack_supply


class _Wallet:
    def __init__(self, minerals: int, vespene: int, supply_left: int) -> None:
        self.minerals = minerals
        self.vespene = vespene
        self.supply_left = supply_left

    def spend(self, item: str, supply: int = 0) -> bool:
        minerals, gas = COST[item]
        if self.minerals < minerals or self.vespene < gas or self.supply_left < supply:
            return False
        self.minerals -= minerals
        self.vespene -= gas
        self.supply_left -= supply
        return True


def decide(state: MacroState, config: PlanConfig = PlanConfig()) -> list:
    """Return the list of actions to take this step, in priority order.

    Spending is tracked so that the actions together never cost more than
    the minerals, gas and supply available.
    """
    actions = []
    wallet = _Wallet(state.minerals, state.vespene, state.supply_left)
    has_pylon = state.pylons > 0

    if state.enemies_near_base > 0:
        actions.append(DEFEND)
    elif next_attack_mode(state, config):
        actions.append(ATTACK)
    elif state.attacking:
        actions.append(RETREAT)

    if pylon_needed(state) and wallet.spend("pylon"):
        actions.append(BUILD_PYLON)

    probes_short = worker_target(state) - state.workers - state.pending_probes
    for _ in range(min(probes_short, state.idle_nexuses)):
        if wallet.spend("probe", supply=1):
            actions.append(TRAIN_PROBE)

    gateways_total = state.gateways + state.gateways_pending
    if (
        has_pylon
        and gateways_total < config.max_gateways
        and state.supply_used >= config.first_gateway_supply
        # After the first Gateway, wait for the Cybernetics Core to start.
        and (gateways_total == 0 or state.cybernetics_core_ready or state.cybernetics_core_pending)
        and wallet.spend("gateway")
    ):
        actions.append(BUILD_GATEWAY)

    if (
        state.gateways > 0
        and not state.cybernetics_core_ready
        and not state.cybernetics_core_pending
        and wallet.spend("cybernetics_core")
    ):
        actions.append(BUILD_CYBERNETICS_CORE)

    assimilators_total = state.assimilators + state.assimilators_pending
    if (
        gateways_total > 0
        and assimilators_total < config.max_assimilators
        and state.supply_used >= config.assimilator_supply
        and wallet.spend("assimilator")
    ):
        actions.append(BUILD_ASSIMILATOR)

    for _ in range(state.idle_gateways):
        if state.cybernetics_core_ready and wallet.spend("stalker", supply=2):
            actions.append(TRAIN_STALKER)
        elif wallet.spend("zealot", supply=2):
            actions.append(TRAIN_ZEALOT)

    return actions
