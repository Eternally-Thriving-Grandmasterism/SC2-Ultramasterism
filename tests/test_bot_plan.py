"""Unit tests for the bot's macro plan (no game needed)."""

import pytest

from sc2um.bot import plan
from sc2um.bot.plan import MacroState, PlanConfig, decide, next_attack_mode, pylon_needed, worker_target


def state(**overrides):
    base = dict(minerals=0, vespene=0, supply_used=12, supply_cap=15, workers=12, army_supply=0, pylons=0)
    base.update(overrides)
    return MacroState(**base)


def test_opening_trains_a_probe():
    assert decide(state(minerals=50)) == [plan.TRAIN_PROBE]


def test_no_probe_without_minerals_or_idle_nexus():
    assert decide(state(minerals=49)) == []
    assert decide(state(minerals=500, idle_nexuses=0, supply_used=13, supply_cap=23)) == []


def test_worker_target_counts_assimilators():
    assert worker_target(state()) == 16
    assert worker_target(state(assimilators=1, assimilators_pending=1)) == 22
    assert worker_target(state(nexus_count=2)) == 32


def test_probes_stop_at_saturation():
    s = state(minerals=1000, workers=16, supply_used=16, supply_cap=31, pylons=1)
    assert plan.TRAIN_PROBE not in decide(s)
    s = state(minerals=1000, workers=15, pending_probes=1, supply_used=16, supply_cap=31, pylons=1)
    assert plan.TRAIN_PROBE not in decide(s)


def test_pylon_when_supply_is_low():
    assert pylon_needed(state(supply_used=13, supply_cap=15))
    assert not pylon_needed(state(supply_used=13, supply_cap=23))
    # one pending pylon is enough early on
    assert not pylon_needed(state(supply_used=14, supply_cap=15, pylons_pending=1))
    # later, two may be pending
    assert pylon_needed(state(supply_used=78, supply_cap=79, pylons_pending=1, gateways=4))
    assert not pylon_needed(state(supply_used=199, supply_cap=200))


def test_pylon_comes_before_probe_when_money_is_short():
    actions = decide(state(minerals=120, supply_used=14, supply_cap=15, workers=14))
    assert actions == [plan.BUILD_PYLON]


def test_gateway_needs_pylon_and_supply():
    s = state(minerals=150, supply_used=14, supply_cap=23, workers=14, idle_nexuses=0)
    assert decide(s) == []  # no pylon yet
    s = state(minerals=150, supply_used=14, supply_cap=23, workers=14, idle_nexuses=0, pylons=1)
    assert decide(s) == [plan.BUILD_GATEWAY]
    s = state(minerals=150, supply_used=13, supply_cap=23, workers=13, idle_nexuses=0, pylons=1)
    assert decide(s) == []


def test_core_then_more_gateways():
    s = state(minerals=300, supply_used=16, supply_cap=23, workers=16, idle_nexuses=0, pylons=1, gateways=1)
    assert decide(s) == [plan.BUILD_CYBERNETICS_CORE, plan.BUILD_ASSIMILATOR]
    s = state(
        minerals=300, supply_used=17, supply_cap=31, workers=17, idle_nexuses=0, pylons=1,
        gateways=1, cybernetics_core_pending=True, assimilators=2,
    )
    assert decide(s) == [plan.BUILD_GATEWAY]


def test_gateway_cap():
    s = state(
        minerals=1000, supply_used=30, supply_cap=47, workers=22, idle_nexuses=0, pylons=2,
        gateways=3, gateways_pending=1, cybernetics_core_ready=True, assimilators=2,
    )
    assert plan.BUILD_GATEWAY not in decide(s)


def test_assimilator_cap():
    s = state(minerals=500, supply_used=20, supply_cap=31, workers=20, idle_nexuses=0, pylons=1,
              gateways=1, cybernetics_core_pending=True, gateways_pending=3, assimilators=1, assimilators_pending=1)
    assert plan.BUILD_ASSIMILATOR not in decide(s)


def test_zealots_before_core_stalkers_after():
    s = state(minerals=300, vespene=0, supply_used=20, supply_cap=39, workers=20, idle_nexuses=0, pylons=2,
              gateways=2, idle_gateways=2, cybernetics_core_pending=True, gateways_pending=2, assimilators=2)
    assert decide(s) == [plan.TRAIN_ZEALOT, plan.TRAIN_ZEALOT]
    s = state(minerals=300, vespene=100, supply_used=20, supply_cap=39, workers=20, idle_nexuses=0, pylons=2,
              gateways=2, idle_gateways=2, cybernetics_core_ready=True, gateways_pending=2, assimilators=2)
    assert decide(s) == [plan.TRAIN_STALKER, plan.TRAIN_STALKER]


def test_falls_back_to_zealot_without_gas():
    s = state(minerals=250, vespene=50, supply_used=22, supply_cap=39, workers=22, idle_nexuses=0, pylons=2,
              gateways=4, idle_gateways=2, cybernetics_core_ready=True, assimilators=2)
    assert decide(s) == [plan.TRAIN_STALKER, plan.TRAIN_ZEALOT]


def test_spending_never_exceeds_bank():
    s = state(minerals=400, vespene=0, supply_used=16, supply_cap=17, workers=15, idle_nexuses=1, pylons=1,
              gateways=1, idle_gateways=1)
    actions = decide(s)
    cost = sum(plan.COST[{"build_pylon": "pylon", "train_probe": "probe", "build_cybernetics_core": "cybernetics_core",
                          "build_assimilator": "assimilator", "train_zealot": "zealot", "build_gateway": "gateway",
                          "train_stalker": "stalker"}[a]][0] for a in actions)
    assert cost <= 400
    # only 1 supply left: no Zealot (2 supply), Probe (1) is fine
    assert plan.TRAIN_ZEALOT not in actions


def test_no_army_unit_without_supply():
    s = state(minerals=500, supply_used=39, supply_cap=39, workers=22, idle_nexuses=0, pylons=3,
              gateways=4, idle_gateways=4, cybernetics_core_ready=True, assimilators=2, pylons_pending=1)
    assert plan.TRAIN_ZEALOT not in decide(s)


@pytest.mark.parametrize(
    "attacking,army,expected",
    [(False, 18, False), (False, 20, True), (True, 8, True), (True, 6, False), (True, 0, False)],
)
def test_attack_hysteresis(attacking, army, expected):
    assert next_attack_mode(state(attacking=attacking, army_supply=army)) is expected


def test_attack_and_retreat_actions():
    assert decide(state(army_supply=20))[0] == plan.ATTACK
    assert decide(state(army_supply=4, attacking=True))[0] == plan.RETREAT
    assert plan.ATTACK not in decide(state(army_supply=10))


def test_defend_overrides_attack():
    actions = decide(state(army_supply=30, enemies_near_base=3))
    assert actions[0] == plan.DEFEND
    assert plan.ATTACK not in actions


def test_custom_config():
    cfg = PlanConfig(attack_supply=8, retreat_supply=2)
    assert decide(state(army_supply=8), cfg)[0] == plan.ATTACK
