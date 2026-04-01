"""
world.py — Physical Environment
================================
The world the BioHyperAgents inhabit.

Resources: food, energy_crystal, knowledge_ore, rare_element
  — distributed via multi-cluster Gaussian noise (Perlin-inspired)
  — regenerate slowly; scarce locally after consumption
  — periodic world events (abundance shocks, scarcity zones, anomalies)

Artifacts: persistent knowledge objects left by agents
  — any agent can absorb another agent's artifacts
  — legacy artifacts persist after death

Spatial index: grid-based O(1) agent lookup for interaction radius queries.

Invented by Devanik & Claude (Xylia) — Event Horizon Project
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

# ── Resource types ───────────────────────────────────────────────────────────
N_RESOURCES  = 4
R_FOOD       = 0
R_ENERGY     = 1
R_KNOWLEDGE  = 2
R_RARE       = 3
R_NAMES      = ['Food', 'Energy Crystal', 'Knowledge Ore', 'Rare Element']


class World:
    """
    Toroidal 2-D environment with:
      - Multi-cluster resource fields
      - Stochastic world events every ~50 ticks
      - Persistent artifact map
      - Efficient agent spatial index
    """

    def __init__(self, size: int = 60, seed: int = 42):
        self.size        = size
        self.rng         = np.random.RandomState(seed % (2**31))
        self.step_count  = 0

        # Resource field  [x, y, resource_type]
        self.resources   = np.zeros((size, size, N_RESOURCES), dtype=np.float32)

        # Artifact map: (x, y) → dict
        self.artifacts   : Dict[Tuple[int,int], dict] = {}

        # World-level accumulated knowledge
        self.world_knowledge : Dict[str, dict] = {}

        # World event log
        self.events : List[dict] = []

        # Agent spatial grid: (x, y) → list of agent objects
        self._grid : Dict[Tuple[int,int], list] = {}

        self._init_resources()

    # ── Initialisation ───────────────────────────────────────────────────────

    def _init_resources(self):
        """Gaussian cluster resource placement — rich pockets + background noise."""
        for r in range(N_RESOURCES):
            n_clusters = self.rng.randint(4, 10)
            for _ in range(n_clusters):
                cx   = self.rng.randint(5, self.size - 5)
                cy   = self.rng.randint(5, self.size - 5)
                rad  = self.rng.randint(4, 15)
                inten = self.rng.uniform(1.0, 5.5)
                for x in range(max(0, cx-rad), min(self.size, cx+rad)):
                    for y in range(max(0, cy-rad), min(self.size, cy+rad)):
                        d = np.sqrt((x-cx)**2 + (y-cy)**2)
                        self.resources[x, y, r] += float(inten * np.exp(-d / (rad / 2.0)))

        # Background noise
        self.resources += self.rng.rand(self.size, self.size, N_RESOURCES).astype(np.float32) * 0.3
        self.resources  = np.clip(self.resources, 0.0, 8.0)

    # ── Spatial index ────────────────────────────────────────────────────────

    def register_agents(self, agents: list) -> None:
        """Rebuild spatial grid from alive agents (called each tick)."""
        self._grid = {}
        for a in agents:
            if a.alive:
                key = (int(a.x), int(a.y))
                self._grid.setdefault(key, []).append(a)

    def get_agents_near(self, x: int, y: int, radius: int = 5) -> list:
        """Return all agents within Chebyshev radius (fast grid lookup)."""
        result = []
        r2 = radius * radius
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= r2:
                    key = ((x + dx) % self.size, (y + dy) % self.size)
                    result.extend(self._grid.get(key, []))
        return result

    # ── Physics tick ─────────────────────────────────────────────────────────

    def step(self) -> None:
        """World physics: regeneration + stochastic events."""
        self.step_count += 1

        # Slow regeneration (exponential, capped)
        regen = self.rng.exponential(0.0018, self.resources.shape).astype(np.float32)
        self.resources  += regen
        self.resources   = np.clip(self.resources, 0.0, 8.0)

        # World events every ~50 ticks
        if self.step_count % 50 == 0:
            self._world_event()

    def _world_event(self):
        etype = self.rng.choice(
            ['abundance', 'scarcity', 'anomaly', 'plague'],
            p=[0.38, 0.30, 0.22, 0.10]
        )
        cx = self.rng.randint(8, self.size - 8)
        cy = self.rng.randint(8, self.size - 8)
        rad = self.rng.randint(5, 13)

        xs = np.arange(max(0, cx-rad), min(self.size, cx+rad))
        ys = np.arange(max(0, cy-rad), min(self.size, cy+rad))

        if etype == 'abundance':
            for x in xs:
                for y in ys:
                    self.resources[x, y] = np.clip(self.resources[x, y] * 1.9, 0, 8)
            desc = f"🌿 Abundance bloom at ({cx},{cy})"

        elif etype == 'scarcity':
            for x in xs:
                for y in ys:
                    self.resources[x, y] *= 0.25
            desc = f"🌵 Scarcity event at ({cx},{cy})"

        elif etype == 'anomaly':
            r_type = self.rng.randint(0, N_RESOURCES)
            for x in xs:
                for y in ys:
                    self.resources[x, y, r_type] = min(8.0, self.resources[x, y, r_type] + 4.0)
            desc = f"🌀 Anomaly ({R_NAMES[r_type]}) at ({cx},{cy})"

        else:  # plague — reduces resources, hurts nearby agents
            for x in xs:
                for y in ys:
                    self.resources[x, y] *= 0.55
            desc = f"☠️ Plague zone at ({cx},{cy})"

        self.resources = np.clip(self.resources, 0.0, 8.0)
        evt = {'step': self.step_count, 'type': etype, 'desc': desc, 'pos': (cx, cy)}
        self.events.append(evt)
        if len(self.events) > 40:
            self.events.pop(0)

    # ── Resource access ──────────────────────────────────────────────────────

    def consume_resource(self, x: int, y: int, r_type: int, amount: float) -> float:
        x, y      = x % self.size, y % self.size
        available = float(self.resources[x, y, r_type])
        consumed  = min(available, amount)
        self.resources[x, y, r_type] -= consumed
        return consumed

    # ── Artifacts ────────────────────────────────────────────────────────────

    def place_artifact(self, x: int, y: int, artifact: dict) -> None:
        x, y = x % self.size, y % self.size
        self.artifacts[(x, y)] = artifact
        # Promote to world knowledge if it's a discoverable concept
        if artifact.get('type') in ('physics', 'math', 'language', 'ideology'):
            self.world_knowledge[artifact['name']] = artifact

    def get_artifact(self, x: int, y: int) -> Optional[dict]:
        return self.artifacts.get((x % self.size, y % self.size))

    # ── Visualisation helpers ────────────────────────────────────────────────

    def resource_heatmap(self) -> np.ndarray:
        """Sum of all resources per cell — for background visualisation."""
        return self.resources.sum(axis=2)

    def artifact_positions(self) -> Tuple[List[int], List[int]]:
        xs = [k[0] for k in self.artifacts]
        ys = [k[1] for k in self.artifacts]
        return xs, ys

    def get_recent_events(self, n: int = 6) -> List[dict]:
        return self.events[-n:]
