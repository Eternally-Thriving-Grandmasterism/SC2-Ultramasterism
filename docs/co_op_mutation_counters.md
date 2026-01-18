# Co-op Mutation Counters Lattice

Powrush Divine mutation branch — mercy-reconcile weekly hazards with commander synergies. Focus Brutal+ (high points). Current (Jan 2026): **Violent Night** (Naughty List: kill stacks boost enemy damage; Gift Exchange: contest gifts for rewards/enemies). Strategy: Aggressive early clears + gift control. Duo Pick: You (Zeratul fast kills) + Astarion (Han&Horner air/econ) = Apex contest.

### Mutation Counters Mermaid Lattice
```mermaid
graph TD
    MutationApex["Mutation Counters Apex<br>Brutal+ Clears Eternal<br>Duo Synergy Thriving"] --> Common["Major Mutations"]

    Common --> BlackDeath["Black Death<br>(Exploding Plague Spread)<br>Air/Regen Heavy"]
    Common --> Propagators["Propagators<br>(Sludge Converters)<br>Fast Hero Burst"]
    Common --> VoidRifts["Void Rifts/Reanimators<br>(Rift Spawns/Revives)<br>Quick Clear AoE"]
    Common --> Polarity["Polarity<br>(Damage Sides)<br>Coordinate Splits"]
    Common --> MissileCommand["Missile Command<br>(Endless Missiles)<br>PDM/Hitscan Overload"]
    Common --> JustDie["Just Die!<br>(Auto Revive)<br>Final Kill Focus"]

    BlackDeath --> Counters1["Nova (Air Stealth)<br>Alarak (Ascendant)<br>Han&Horner (Air Fleet)"]
    Propagators --> Counters2["Tychus (Heroes)<br>Zeratul (Legends)"]
    VoidRifts --> Counters3["Zeratul (Artifact Rush)<br>Dehaka (Primal Pack)"]
    Polarity --> Counters4["Mixed Comps<br>Vorazun (Stasis/Confusion)"]
    MissileCommand --> Counters5["Hitscan (Stetmann Gary)<br>Time Stop (Vorazun)"]
    JustDie --> Counters6["Burst Finals<br>Abathur/Dehaka (Resource on Final)"]

    MutationApex --> Duo["Eternal Duo Picks (Protoss + Terran)"]
    Duo --> DuoBlack["Black Death: You (Nova equiv air) + Astarion (Tychus heroes)"]
    Duo --> DuoProp["Propagators: You (Zeratul) + Astarion (Swann mech)"]
    Duo --> DuoRifts["Rifts: You (Fenix suits) + Astarion (Raynor bio)"]

    style MutationApex fill:#1e3a8a,stroke:#fff,color:#fff
    style Duo fill:#7c3aed,stroke:#fff,color:#fff
