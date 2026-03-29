"""
evolution.py — Population Lifecycle Engine
==========================================
Manages the full lifecycle of the BioHyperAgent population:
  - Initial seeding of 128 agents with maximally diverse spectral identities
  - Processing births (from agent reproduction actions)
  - Processing deaths (starvation / combat / old age)
  - Population floor (auto-immigration if population crashes)
  - Population ceiling (hard cap prevents runaway growth)
  - Generation and lineage tracking
  - Per-tick statistics for visualisation

Invented by Devanik & Claude (Xylia) — Event Horizon Project
"""

import numpy as np
from typing import Dict, List, Tuple, Optional

from agents import BioHyperAgent
from world import World
from civilization import CivilizationManager


class EvolutionEngine:
    """
    The outer loop that drives the entire simulation.

    Call initialize() once, then call process_step() every tick.
    All agent births, deaths, world steps, and civilisation updates
    are orchestrated from here.
    """

    INITIAL_POP = 128
    MAX_POP     = 200
    MIN_POP     = 18

    def __init__(self, world_size: int = 60, seed: int = 42):
        self.world_size = world_size
        self.seed       = seed
        self.rng        = np.random.RandomState(seed % (2**31))

        self.agents      : Dict[str, BioHyperAgent] = {}

        # Population bookkeeping
        self.total_born  : int  = 0
        self.total_died  : int  = 0
        self.generation  : int  = 0   # max generation in population

        # History for charts
        self.pop_history    : List[int]   = []
        self.energy_history : List[float] = []
        self.inv_history    : List[int]   = []

        # Lineage map: agent_id → [child_ids]
        self.lineage : Dict[str, List[str]] = {}

    # ── Seeding ──────────────────────────────────────────────────────────────

    def initialize(self) -> Dict[str, BioHyperAgent]:
        """
        Spawn 128 initial agents with maximally diverse spectral identities.
        Agents are scattered across the world to prevent early clustering.
        """
        agents = {}
        for i in range(self.INITIAL_POP):
            x = self.rng.randint(2, self.world_size - 2)
            y = self.rng.randint(2, self.world_size - 2)
            a = BioHyperAgent(
                x=x, y=y,
                world_size=self.world_size,
                seed=self.seed + i * 41 + 7,
                generation=0,
            )
            # Stagger energy for initial diversity
            a.energy = self.rng.uniform(2.5, 6.5)
            agents[a.id] = a
            self.lineage[a.id] = []

        self.agents     = agents
        self.total_born = self.INITIAL_POP
        return agents

    # ── Main tick ────────────────────────────────────────────────────────────

    def process_step(
        self,
        world     : World,
        civ       : CivilizationManager,
    ) -> Tuple[Dict[str, BioHyperAgent], List[str]]:
        """
        One simulation tick:
          1. Rebuild spatial index
          2. Step every alive agent (sense → decide → act → learn → evolve)
          3. Collect newborns
          4. Remove dead agents
          5. Enforce population floor (immigration)
          6. World physics tick
          7. Civilisation update
          8. Record statistics

        Returns (agents_dict, event_strings_list)
        """
        events : List[str] = []
        new_children : List[BioHyperAgent] = []

        # Snapshot alive agents for this tick
        alive = {aid: a for aid, a in self.agents.items() if a.alive}
        world.register_agents(list(alive.values()))

        # Step all alive agents
        for agent in list(alive.values()):
            try:
                child = agent.step(world, alive)
            except Exception:
                child = None

            if child is not None:
                new_children.append(child)
                self.lineage.setdefault(agent.id, []).append(child.id)

        # Add newborns (respect ceiling)
        for child in new_children:
            if len(self.agents) < self.MAX_POP:
                self.agents[child.id]  = child
                self.lineage[child.id] = []
                self.total_born       += 1
                self.generation        = max(self.generation, child.generation)
                events.append(f"🐣 Born: {child.id} ← {child.parent_ids[0][:6]}")

        # Remove dead
        dead = [aid for aid, a in self.agents.items() if not a.alive]
        for did in dead:
            age = self.agents[did].age
            events.append(f"💀 Died: {did[:6]} (age {age})")
            del self.agents[did]
            self.total_died += 1

        # Population floor — spawn immigrants
        n_alive = len(self.agents)
        if n_alive < self.MIN_POP:
            for _ in range(self.MIN_POP - n_alive):
                immigrant = self._spawn_immigrant()
                self.agents[immigrant.id]  = immigrant
                self.lineage[immigrant.id] = []
                self.total_born           += 1
                events.append(f"🌍 Immigrant: {immigrant.id}")

        # World and civilisation tick
        world.step()
        civ.update(self.agents, world.step_count)

        # Stats bookkeeping
        alive_now = [a for a in self.agents.values() if a.alive]
        self.pop_history.append(len(alive_now))
        if alive_now:
            self.energy_history.append(float(np.mean([a.energy for a in alive_now])))
            self.inv_history.append(int(sum(len(a.brain.discoveries) for a in alive_now)))
        if len(self.pop_history) > 600:
            self.pop_history.pop(0)
            self.energy_history.pop(0)
            self.inv_history.pop(0)

        return self.agents, events

    # ── Utilities ────────────────────────────────────────────────────────────

    def _spawn_immigrant(self) -> BioHyperAgent:
        """Spawn a fresh agent at a random world edge."""
        side = self.rng.randint(4)
        if   side == 0: x, y = 0,                    self.rng.randint(0, self.world_size)
        elif side == 1: x, y = self.world_size - 1,  self.rng.randint(0, self.world_size)
        elif side == 2: x, y = self.rng.randint(0, self.world_size), 0
        else          : x, y = self.rng.randint(0, self.world_size), self.world_size - 1

        a        = BioHyperAgent(x=x, y=y, world_size=self.world_size,
                                  seed=self.rng.randint(0, 2**31))
        a.energy = 3.0
        return a

    def get_stats(self) -> dict:
        alive = [a for a in self.agents.values() if a.alive]
        n     = len(alive)
        if n == 0:
            return {'n_alive': 0, 'total_born': self.total_born,
                    'total_died': self.total_died, 'pop_history': self.pop_history}

        energies     = [a.energy for a in alive]
        ages         = [a.age    for a in alive]
        total_inv    = sum(len(a.brain.discoveries)   for a in alive)
        total_kills  = sum(a.n_kills                  for a in alive)
        total_kids   = sum(a.n_children               for a in alive)
        avg_rep      = float(np.mean([a.reputation    for a in alive]))

        return {
            'n_alive'       : n,
            'total_born'    : self.total_born,
            'total_died'    : self.total_died,
            'max_generation': self.generation,
            'avg_energy'    : round(float(np.mean(energies)), 2),
            'max_energy'    : round(float(np.max(energies)), 2),
            'avg_age'       : round(float(np.mean(ages)), 1),
            'max_age'       : int(np.max(ages)),
            'total_inv'     : total_inv,
            'total_kills'   : total_kills,
            'total_kids'    : total_kids,
            'avg_reputation': round(avg_rep, 2),
            'pop_history'   : self.pop_history[-150:],
            'energy_history': self.energy_history[-150:],
            'inv_history'   : self.inv_history[-150:],
        }

    def top_agents(self, key: str = 'energy', n: int = 10) -> List[dict]:
        alive = [a for a in self.agents.values() if a.alive]
        key_fn = {
            'energy'     : lambda a: a.energy,
            'age'        : lambda a: a.age,
            'inventions' : lambda a: len(a.brain.discoveries),
            'kills'      : lambda a: a.n_kills,
            'children'   : lambda a: a.n_children,
            'reputation' : lambda a: a.reputation,
            'wonder'     : lambda a: float(a.brain.emotions[6]),
        }.get(key, lambda a: a.energy)

        return [a.to_dict() for a in sorted(alive, key=key_fn, reverse=True)[:n]]
