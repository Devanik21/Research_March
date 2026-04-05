"""
world.py — Hyper-Horizon World Physics v3.0
=============================================
The physical substrate in which BioHyperAgents live, die, and evolve.

Resources   : 4 species on a toroidal grid (R_FOOD, R_MINERAL, R_KNOWLEDGE, R_RARE)
Knowledge   : Diffusing 'idea field' — inspiration gradient
Artifacts   : Physical relics of agent invention
Events      : Stochastic world perturbations

NEW in v3.0 (ported from GeNeSIS / Thermodynamic-Mind):
  PhysicsOracle  : Frozen PyTorch NN — agents reverse-engineer reality
  Pheromones     : 8-channel diffusing chemical signal grid (stigmergy)
  Meme Grid      : 3-channel stigmergic cultural memory (Danger/Resource/Sacred)
  Seasons        : Summer/Winter cycle with resource modulation
  Social Bonds   : Persistent frozenset pairs with metabolic osmosis
  Structures     : Trap, Battery, Cultivator — functional world objects
  Weather Control: Collective agent votes modulate season intensity
  Adaptive Spawn : Resource spawn rate inversely proportional to population
  MegaResource   : Cooperative-harvest resource requiring multiple agents

Invented by Devanik & Claude (Xylia) — Event Horizon Project
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional, Set

# ── Resource types ──────────────────────────────────────────────────────────
N_RESOURCES  = 4
R_FOOD       = 0
R_MINERAL    = 1
R_KNOWLEDGE  = 2
R_RARE       = 3

# ════════════════════════════════════════════════════════════════════════════
# NEW v3.0: PHYSICS ORACLE — THE BLACK BOX OF REALITY
# ════════════════════════════════════════════════════════════════════════════

class PhysicsOracle(nn.Module):
    """
    A frozen neural network that defines the 'laws of physics' for the world.
    Weights are fixed at initialisation (orthogonal init, fixed seed).
    Agents must learn to reverse-engineer this oracle.

    Input:  (21D agent_vector, 16D local_signal) = 37D
    Output: (energy_flux, dx_bias, dy_bias, transmute_factor, drain_factor) = 5D
    """
    def __init__(self, seed: int = 314159):
        super().__init__()
        torch.manual_seed(seed)
        self.layers = nn.Sequential(
            nn.Linear(37, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.SiLU(),
            nn.Linear(64, 5),
        )
        # Orthogonal init for maximum information preservation
        for m in self.layers.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=1.5)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)
        # Specific bias tweaks
        with torch.no_grad():
            self.layers[-1].bias[0] = 0.0   # energy_flux neutral
            self.layers[-1].bias[4] = -0.3  # drain slightly negative

        # FREEZE all parameters
        for p in self.parameters():
            p.requires_grad = False
        self.eval()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


# ════════════════════════════════════════════════════════════════════════════
# NEW v3.0: STRUCTURE CLASSES (ported from GeNeSIS)
# ════════════════════════════════════════════════════════════════════════════

class Structure:
    """Agent-built persistent world object that modifies the environment."""
    def __init__(self, x: int, y: int, struct_type: str, builder_id: str):
        self.x           = x
        self.y           = y
        self.struct_type = struct_type
        self.builder_id  = builder_id
        self.age         = 0
        self.durability  = 100.0
        self.created_tick= 0

    def decay(self, rate: float = 0.05) -> bool:
        """Returns True if still standing."""
        self.age += 1
        self.durability -= rate
        return self.durability > 0


class Trap(Structure):
    """Harvests energy from non-builder agents passing through."""
    def __init__(self, x: int, y: int, builder_id: str,
                 harvest_rate: float = 0.2):
        super().__init__(x, y, "trap", builder_id)
        self.harvest_rate  = min(0.5, harvest_rate)
        self.stored_energy = 0.0

    def harvest(self, agent_id: str, agent_energy: float) -> float:
        """Harvest from non-builder. Returns energy taken."""
        if agent_id == self.builder_id:
            return 0.0
        taken = agent_energy * self.harvest_rate
        self.stored_energy += taken
        return taken

    def collect(self, agent_id: str) -> float:
        """Builder collects stored energy."""
        if agent_id == self.builder_id:
            collected = self.stored_energy * 0.9
            self.stored_energy *= 0.1
            return collected
        return 0.0


class Battery(Structure):
    """Stores energy for later retrieval by authorised agents."""
    def __init__(self, x: int, y: int, builder_id: str,
                 capacity: float = 500.0):
        super().__init__(x, y, "battery", builder_id)
        self.capacity     = capacity
        self.stored_energy= 0.0
        self.authorized   : Set[str] = {builder_id}

    def deposit(self, amount: float) -> float:
        """Deposit energy. Returns how much was accepted."""
        space  = max(0.0, self.capacity - self.stored_energy)
        actual = min(amount, space)
        self.stored_energy += actual * 0.9  # 10% loss
        return actual

    def withdraw(self, agent_id: str) -> float:
        """Authorised withdrawal."""
        if agent_id in self.authorized:
            amount = self.stored_energy * 0.9
            self.stored_energy *= 0.1
            return amount
        return 0.0


class Cultivator(Structure):
    """Boosts resource spawn rate in surrounding tiles."""
    def __init__(self, x: int, y: int, builder_id: str,
                 boost_radius: int = 2, boost_strength: float = 0.3):
        super().__init__(x, y, "cultivator", builder_id)
        self.boost_radius   = boost_radius
        self.boost_strength = boost_strength

    def get_influenced_tiles(self, world_size: int) -> List[Tuple[int, int]]:
        tiles = []
        for dx in range(-self.boost_radius, self.boost_radius + 1):
            for dy in range(-self.boost_radius, self.boost_radius + 1):
                tiles.append(((self.x + dx) % world_size,
                              (self.y + dy) % world_size))
        return tiles


class MegaResource:
    """A high-value resource requiring cooperative harvest (multiple agents)."""
    def __init__(self, x: int, y: int, value: float = 150.0,
                 required_agents: int = 2):
        self.x               = x
        self.y               = y
        self.value           = value
        self.required_agents = required_agents


# ════════════════════════════════════════════════════════════════════════════
# WORLD
# ════════════════════════════════════════════════════════════════════════════

class World:
    """
    The physical substrate:
      - Toroidal grid of resources, knowledge, pheromones, memes
      - Oracle physics for genuine discovery pressure
      - Structures (Trap, Battery, Cultivator)
      - Seasonal and weather dynamics
      - Bond registry with metabolic osmosis
      - MegaResources for cooperative incentives
    """

    SEASON_LENGTH = 50   # ticks per season

    def __init__(self, size: int = 60, seed: int = 42):
        self.size       = size
        self.rng        = np.random.RandomState(seed % (2**31))
        self.step_count = 0

        # ── Core resource grid ────────────────────────────────────────────
        self.resources = (
            self.rng.exponential(0.5, (size, size, N_RESOURCES))
            .astype(np.float32)
        )

        # ── Knowledge field ───────────────────────────────────────────────
        self.knowledge_field = np.zeros((size, size), dtype=np.float32)

        # ── Artifact storage ──────────────────────────────────────────────
        self.artifacts: Dict[Tuple[int, int], dict] = {}

        # ── Spatial index ─────────────────────────────────────────────────
        self._agent_grid: Dict[Tuple[int, int], list] = {}

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: PhysicsOracle (frozen, deterministic)
        # ══════════════════════════════════════════════════════════════════
        self.oracle = PhysicsOracle(seed=seed)

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Pheromone Grid (8 chemical channels)
        # ══════════════════════════════════════════════════════════════════
        self.pheromone_grid = np.zeros((size, size, 8), dtype=np.float32)

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Meme Grid — Stigmergic Memory (3 channels)
        #   Channel 0 = Danger, Channel 1 = Resource, Channel 2 = Sacred
        # ══════════════════════════════════════════════════════════════════
        self.meme_grid = np.zeros((size, size, 3), dtype=np.float32)

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Seasonal Dynamics
        # ══════════════════════════════════════════════════════════════════
        self.season       : int   = 0      # 0=Summer, 1=Winter, ...
        self.season_timer : int   = 0
        self.env_phase    : float = 0.0    # Circadian phase for agents
        self.weather_amplitude: float = 1.0

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Social Bond Registry
        # ══════════════════════════════════════════════════════════════════
        self.bonds: Set[frozenset] = set()

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Structures (Trap, Battery, Cultivator)
        # ══════════════════════════════════════════════════════════════════
        self.structures    : Dict[Tuple[int, int], Structure] = {}
        self.cultivator_map: Dict[Tuple[int, int], float]     = {}

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: MegaResources (cooperative harvest)
        # ══════════════════════════════════════════════════════════════════
        self.mega_resources: Dict[Tuple[int, int], MegaResource] = {}

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Collective metrics
        # ══════════════════════════════════════════════════════════════════
        self.kuramoto_order_parameter: float = 0.0
        self.population_count        : int   = 0

        # ══════════════════════════════════════════════════════════════════
        # Event log for frontend events feed
        # ══════════════════════════════════════════════════════════════════
        self._event_log: List[dict] = []

    # ── Agent spatial index ──────────────────────────────────────────────────

    def register_agents(self, agents: list) -> None:
        """Rebuild the spatial grid index every tick."""
        self._agent_grid = {}
        for a in agents:
            key = (a.x % self.size, a.y % self.size)
            self._agent_grid.setdefault(key, []).append(a)
        self.population_count = len(agents)

    def get_agents_near(self, x: int, y: int, radius: int = 3) -> list:
        """Find agents within Manhattan radius (fast grid scan)."""
        result = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                key = ((x + dx) % self.size, (y + dy) % self.size)
                result.extend(self._agent_grid.get(key, []))
        return result

    # ── Main step ────────────────────────────────────────────────────────────

    def step(self, agents: dict = None) -> None:
        """
        One world tick (N-tick staggered execution for performance):
          Every tick:  resource regen, pheromone diffusion
          Every 3:     structure processing, cultivator spawn
          Every 5:     weather control, meme grid diffusion
          Every 50:    world events
          Every 100:   MegaResource spawn
        """
        self.step_count += 1

        # ── Seasonal update ───────────────────────────────────────────────
        self.season_timer += 1
        self.env_phase = (self.step_count / self.SEASON_LENGTH) * 2 * np.pi
        if self.season_timer >= self.SEASON_LENGTH:
            self.season += 1
            self.season_timer = 0
        is_winter = (self.season % 2 == 1)

        # ── Adaptive resource regeneration ────────────────────────────────
        n_pop = len(agents) if agents else self.population_count
        adaptive_rate = 1.0 + 10.0 * np.exp(-n_pop / 100.0) if n_pop > 0 else 1.0
        season_mod = 0.6 if is_winter else 1.0
        season_mod *= self.weather_amplitude

        regen = self.rng.exponential(
            0.025 * adaptive_rate * season_mod, self.resources.shape
        ).astype(np.float32)
        self.resources += regen
        np.clip(self.resources, 0.0, 15.0, out=self.resources)

        # ── Knowledge field diffusion (every tick) ────────────────────────
        self._diffuse_knowledge_field()

        # ── Pheromone diffusion (every tick) ──────────────────────────────
        self._diffuse_pheromones()

        # ── Idea interference (every tick) ────────────────────────────────
        self._compute_interference()

        # ── Meme grid diffusion (staggered: every 5) ─────────────────────
        if self.step_count % 5 == 0:
            self._diffuse_meme_grid()

        # ── Structure processing (staggered: every 3) ────────────────────
        if self.step_count % 3 == 0:
            self.process_structures(agents)

        # ── Metabolic osmosis for bonds (every tick) ──────────────────────
        if agents:
            self.metabolic_osmosis(agents)

        # ── Weather control (staggered: every 5) ─────────────────────────
        if self.step_count % 5 == 0 and agents:
            self.update_weather_control(agents)

        # ── World events (staggered: every 50) ───────────────────────────
        if self.step_count % 50 == 0:
            self._world_event()

        # ── MegaResource spawn (staggered: every 100) ────────────────────
        if self.step_count % 100 == 0:
            self.spawn_mega_resource()

        # ── Cultivator-boosted spawn (staggered: every 3, offset) ────────
        if self.step_count % 3 == 1:
            for pos, boost in self.cultivator_map.items():
                if self.rng.random() < boost * 0.1:
                    r_type = self.rng.randint(0, N_RESOURCES)
                    self.resources[pos[0], pos[1], r_type] = min(
                        15.0, self.resources[pos[0], pos[1], r_type] + 3.0
                    )

        # ── Kuramoto order parameter (staggered: every 10) ───────────────
        if self.step_count % 10 == 0 and agents:
            self._compute_kuramoto_order(agents)

    # ── Resource access ──────────────────────────────────────────────────────

    def consume_resource(self, x: int, y: int,
                         r_type: int, amount: float) -> float:
        bx, by = x % self.size, y % self.size
        available = float(self.resources[bx, by, r_type])
        consumed  = min(available, amount)
        self.resources[bx, by, r_type] -= consumed
        return consumed

    # ── Knowledge field ──────────────────────────────────────────────────────

    def get_knowledge_field(self, x: int, y: int) -> float:
        return float(self.knowledge_field[x % self.size, y % self.size])

    def boost_knowledge_field(self, x: int, y: int, amount: float) -> None:
        bx, by = x % self.size, y % self.size
        self.knowledge_field[bx, by] = min(
            5.0, self.knowledge_field[bx, by] + amount
        )

    def _diffuse_knowledge_field(self) -> None:
        kf = self.knowledge_field
        new_kf = (
            kf
            + np.roll(kf, 1, 0) + np.roll(kf, -1, 0)
            + np.roll(kf, 1, 1) + np.roll(kf, -1, 1)
        ) / 5.0
        self.knowledge_field = new_kf * 0.997  # slow evaporation

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: PHYSICS ORACLE INTERFACE
    # ══════════════════════════════════════════════════════════════════════════

    def query_oracle(self, vector_21: np.ndarray,
                     local_signal_16: np.ndarray) -> np.ndarray:
        """
        Query the frozen PhysicsOracle.
        Input:  21D agent vector + 16D local signal = 37D
        Output: 5D (energy_flux, dx, dy, transmute, drain)
        """
        with torch.no_grad():
            v = torch.tensor(vector_21[:21], dtype=torch.float32).unsqueeze(0)
            s = torch.tensor(local_signal_16[:16], dtype=torch.float32).unsqueeze(0)
            inp = torch.cat([v, s], dim=1)
            effects = self.oracle(inp)[0]
        return effects.numpy()

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: PHEROMONE GRID (8-channel stigmergy)
    # ══════════════════════════════════════════════════════════════════════════

    def get_pheromone(self, x: int, y: int) -> np.ndarray:
        return self.pheromone_grid[x % self.size, y % self.size].copy()

    def deposit_pheromone(self, x: int, y: int, signal: np.ndarray) -> None:
        bx, by = x % self.size, y % self.size
        n = min(len(signal), 8)
        self.pheromone_grid[bx, by, :n] += signal[:n]
        np.clip(self.pheromone_grid[bx, by], 0.0, 1.0,
                out=self.pheromone_grid[bx, by])

    def _diffuse_pheromones(self) -> None:
        """Pheromone diffusion: average with 4 neighbours, then evaporate 5%."""
        g = self.pheromone_grid
        diffused = (
            g
            + np.roll(g, 1, 0) + np.roll(g, -1, 0)
            + np.roll(g, 1, 1) + np.roll(g, -1, 1)
        ) / 5.0
        self.pheromone_grid = diffused * 0.95  # 5% evaporation

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: MEME GRID (3-channel stigmergic cultural memory)
    # ══════════════════════════════════════════════════════════════════════════

    def get_meme(self, x: int, y: int) -> np.ndarray:
        return self.meme_grid[x % self.size, y % self.size].copy()

    def deposit_meme(self, x: int, y: int, channel: int,
                     value: float) -> None:
        bx, by = x % self.size, y % self.size
        self.meme_grid[bx, by, channel] = min(
            1.0, self.meme_grid[bx, by, channel] + value
        )

    def _diffuse_meme_grid(self) -> None:
        """Meme diffusion: 9-cell average + slow decay."""
        mg = self.meme_grid
        new_mg = np.zeros_like(mg)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                new_mg += np.roll(np.roll(mg, dx, axis=0), dy, axis=1)
        new_mg /= 9.0
        self.meme_grid = 0.60 * new_mg + 0.40 * mg
        self.meme_grid *= 0.99  # 1% decay per diffusion step
        np.clip(self.meme_grid, 0.0, 1.0, out=self.meme_grid)

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: SOCIAL BOND REGISTRY + METABOLIC OSMOSIS
    # ══════════════════════════════════════════════════════════════════════════

    def form_bond(self, id_a: str, id_b: str) -> None:
        self.bonds.add(frozenset([id_a, id_b]))

    def break_bond(self, id_a: str, id_b: str) -> None:
        self.bonds.discard(frozenset([id_a, id_b]))

    def get_bonded_partners(self, agent_id: str) -> List[str]:
        partners = []
        for bond in self.bonds:
            if agent_id in bond:
                partner = list(bond - {agent_id})
                if partner:
                    partners.append(partner[0])
        return partners

    def metabolic_osmosis(self, agents: dict) -> float:
        """
        Energy equalization between bonded agents.
        Flow rate: 5% of difference, kinship-modulated efficiency.
        """
        dissipated = 0.0
        dead_bonds = []
        for bond in self.bonds:
            ids = list(bond)
            if len(ids) != 2:
                continue
            id_a, id_b = ids
            a = agents.get(id_a)
            b = agents.get(id_b)
            if not a or not b or not a.alive or not b.alive:
                dead_bonds.append(bond)
                continue

            # Flow from high to low
            if a.energy > b.energy:
                donor, receiver = a, b
            else:
                donor, receiver = b, a

            delta = (donor.energy - receiver.energy) * 0.05
            # Tribal kinship modulates efficiency
            kinship = 1.0 if (a.tribe_id and a.tribe_id == b.tribe_id) else 0.5
            efficiency = 0.5 + 0.5 * kinship

            if donor.energy > delta:
                donor.energy    -= delta
                receiver.energy += delta * efficiency
                dissipated      += delta * (1.0 - efficiency)

        # Clean dead bonds
        for bond in dead_bonds:
            self.bonds.discard(bond)

        return dissipated

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: STRUCTURE MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════════

    def add_structure(self, x: int, y: int, struct_type: str,
                      builder_id: str, **kwargs) -> bool:
        key = (x % self.size, y % self.size)
        if key in self.structures:
            return False

        if struct_type == "trap":
            self.structures[key] = Trap(
                key[0], key[1], builder_id,
                kwargs.get("harvest_rate", 0.2)
            )
        elif struct_type == "battery":
            self.structures[key] = Battery(key[0], key[1], builder_id)
        elif struct_type == "cultivator":
            self.structures[key] = Cultivator(key[0], key[1], builder_id)
            self._update_cultivator_map()
        else:
            self.structures[key] = Structure(
                key[0], key[1], struct_type, builder_id
            )

        self.structures[key].created_tick = self.step_count
        return True

    def _update_cultivator_map(self) -> None:
        self.cultivator_map = {}
        for (x, y), struct in self.structures.items():
            if isinstance(struct, Cultivator):
                for tile in struct.get_influenced_tiles(self.size):
                    current = self.cultivator_map.get(tile, 0.0)
                    self.cultivator_map[tile] = min(
                        1.0, current + struct.boost_strength
                    )

    def process_structures(self, agents: dict = None) -> None:
        """Process structure effects: decay, trap harvest."""
        to_remove = []
        for key, struct in self.structures.items():
            if not struct.decay(0.05):
                to_remove.append(key)
                continue

            # Trap: harvest passing agents
            if isinstance(struct, Trap) and agents:
                for a in agents.values():
                    if a.alive and (a.x % self.size, a.y % self.size) == key:
                        taken = struct.harvest(a.id, a.energy)
                        if taken > 0:
                            a.energy -= taken

            # Battery auto-interaction
            if isinstance(struct, Battery) and agents:
                if struct.stored_energy < 0:
                    struct.stored_energy = 0.0
                for a in agents.values():
                    if a.alive and (a.x % self.size, a.y % self.size) == key:
                        if a.energy > 8.0:
                            struct.deposit(1.0)
                        elif a.energy < 3.0:
                            withdrawn = struct.withdraw(a.id)
                            a.energy = min(10.0, a.energy + withdrawn)

        for key in to_remove:
            del self.structures[key]
        if to_remove:
            self._update_cultivator_map()

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: WEATHER CONTROL (collective agent votes)
    # ══════════════════════════════════════════════════════════════════════════

    def update_weather_control(self, agents: dict) -> None:
        if not agents:
            return
        votes = [getattr(a, 'weather_vote', 0.0)
                 for a in agents.values() if a.alive]
        if votes:
            avg_vote = np.mean(votes)
            target = 1.0 + avg_vote * 0.5
            self.weather_amplitude = (
                self.weather_amplitude * 0.95 + target * 0.05
            )

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: MEGA RESOURCE (cooperative harvest)
    # ══════════════════════════════════════════════════════════════════════════

    def spawn_mega_resource(self) -> None:
        x = self.rng.randint(0, self.size)
        y = self.rng.randint(0, self.size)
        self.mega_resources[(x, y)] = MegaResource(x, y)
        # Boost knowledge field at mega site
        self.boost_knowledge_field(x, y, 3.0)

    def attempt_mega_harvest(self, x: int, y: int,
                             agents_at_pos: list) -> float:
        """
        Try to harvest a MegaResource. Returns energy per agent if success.
        Requires >= required_agents at the position.
        """
        key = (x % self.size, y % self.size)
        mega = self.mega_resources.get(key)
        if mega is None:
            return 0.0
        if len(agents_at_pos) >= mega.required_agents:
            share = mega.value / len(agents_at_pos)
            del self.mega_resources[key]
            return share
        return 0.0

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: KURAMOTO ORDER PARAMETER
    # ══════════════════════════════════════════════════════════════════════════

    def _compute_kuramoto_order(self, agents: dict) -> None:
        """Calculate global Kuramoto order parameter: r = |⟨e^{iθ}⟩|."""
        phases = [getattr(a, 'kuramoto_phase', 0.0)
                  for a in agents.values() if a.alive]
        if len(phases) > 1:
            complex_order = np.mean([np.exp(1j * p) for p in phases])
            self.kuramoto_order_parameter = float(abs(complex_order))
        else:
            self.kuramoto_order_parameter = 0.0

    # ── Interference ─────────────────────────────────────────────────────────

    def _compute_interference(self) -> None:
        """Knowledge field constructive/destructive interference."""
        kf = self.knowledge_field
        shift_x = np.roll(kf, 1, 0)
        shift_y = np.roll(kf, 1, 1)
        interference = 0.05 * np.sin(kf * np.pi * 2) * np.cos(
            shift_x * np.pi * 2
        )
        self.knowledge_field += interference
        np.clip(self.knowledge_field, 0.0, 5.0, out=self.knowledge_field)

    # ── World events ─────────────────────────────────────────────────────────

    def _world_event(self) -> None:
        """Stochastic world event: abundance burst or scarcity drought."""
        event_type = self.rng.choice([
            'abundance', 'scarcity', 'knowledge_bloom',
            'resource_shift', 'nothing'
        ])
        desc = f"World: {event_type}"
        if event_type == 'abundance':
            cx, cy = self.rng.randint(0, self.size, 2)
            for dx in range(-6, 7):
                for dy in range(-6, 7):
                    bx = (cx + dx) % self.size
                    by = (cy + dy) % self.size
                    self.resources[bx, by] += self.rng.exponential(1.0, N_RESOURCES)
            np.clip(self.resources, 0, 15, out=self.resources)
            desc = f"🌱 Abundance burst @ ({cx},{cy})"
        elif event_type == 'scarcity':
            cx, cy = self.rng.randint(0, self.size, 2)
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    bx = (cx + dx) % self.size
                    by = (cy + dy) % self.size
                    self.resources[bx, by] *= 0.25
            desc = f"☃️ Scarcity drought @ ({cx},{cy})"
        elif event_type == 'knowledge_bloom':
            cx, cy = self.rng.randint(0, self.size, 2)
            self.boost_knowledge_field(cx, cy, 4.0)
            desc = f"✨ Knowledge bloom @ ({cx},{cy})"
        elif event_type == 'resource_shift':
            shift = self.rng.randint(1, 4)
            self.resources = np.roll(self.resources, shift, axis=0)
            desc = f"🌀 Resource grid shift ×{shift}"
        if event_type != 'nothing':
            self._event_log.append({
                'step': self.step_count, 'type': event_type,
                'desc': desc, 'pos': (0, 0)
            })
            if len(self._event_log) > 200:
                self._event_log.pop(0)

    # ── Artifact access ──────────────────────────────────────────────────────

    def place_artifact(self, x: int, y: int, art: dict) -> None:
        key = (x % self.size, y % self.size)
        self.artifacts[key] = art

    def get_artifact(self, x: int, y: int) -> Optional[dict]:
        return self.artifacts.get((x % self.size, y % self.size))

    # ── Stats ────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            'step'                  : self.step_count,
            'total_resources'       : float(self.resources.sum()),
            'n_artifacts'           : len(self.artifacts),
            'knowledge_avg'         : float(self.knowledge_field.mean()),
            'season'                : 'Winter' if self.season % 2 == 1 else 'Summer',
            'weather_amplitude'     : round(self.weather_amplitude, 3),
            'n_bonds'               : len(self.bonds),
            'n_structures'          : len(self.structures),
            'n_mega_resources'      : len(self.mega_resources),
            'kuramoto_order'        : round(self.kuramoto_order_parameter, 4),
            'pheromone_activity'    : float(self.pheromone_grid.sum()),
            'meme_activity'         : float(self.meme_grid.sum()),
        }

    # ── Frontend compatibility methods ───────────────────────────────────────

    def resource_heatmap(self) -> np.ndarray:
        """Sum all 4 resource layers → (size, size) heatmap for world map view."""
        return self.resources.sum(axis=2)

    def artifact_positions(self) -> Tuple[List[int], List[int]]:
        """Return (xs, ys) lists of artifact coordinates."""
        xs = [pos[0] for pos in self.artifacts]
        ys = [pos[1] for pos in self.artifacts]
        return xs, ys

    def knowledge_field_heatmap(self) -> np.ndarray:
        """Return knowledge field grid (size, size) for frontend heatmap."""
        return self.knowledge_field.copy()

    def get_recent_events(self, n: int = 20) -> List[dict]:
        """Return recent world events for frontend events feed."""
        return list(reversed(self._event_log[-n:])) if hasattr(self, '_event_log') else []

    def get_local_signal(self, x: int, y: int) -> np.ndarray:
        """
        Build 16D local signal vector for Oracle query and sensing.
        Combines resources, knowledge, pheromones.
        """
        bx, by = x % self.size, y % self.size
        sig = np.zeros(16, dtype=float)
        sig[:4]  = self.resources[bx, by]
        sig[4]   = self.knowledge_field[bx, by]
        sig[5:13] = self.pheromone_grid[bx, by]
        sig[13]  = self.meme_grid[bx, by, 0]  # danger
        sig[14]  = self.meme_grid[bx, by, 1]  # resource
        sig[15]  = self.meme_grid[bx, by, 2]  # sacred
        return sig

    @property
    def world_knowledge(self) -> dict:
        """Compatibility property: return artifact names as 'world knowledge' dict."""
        wk = {}
        for (x, y), art in self.artifacts.items():
            name = art.get('name', '?')
            wk[name] = art
        return wk

    @property
    def global_memory(self) -> 'GlobalMemoryStub':
        """Compatibility property for legacy frontend calls."""
        if not hasattr(self, '_global_memory_stub'):
            self._global_memory_stub = GlobalMemoryStub(self)
        return self._global_memory_stub


class GlobalMemoryStub:
    """Compatibility stub for frontend calls to W.global_memory."""
    def __init__(self, world: 'World'):
        self._world = world
        self.count  = 0

    def spectral_summary(self) -> np.ndarray:
        """Return a spectral summary from the knowledge field."""
        return np.abs(np.fft.rfft(self._world.knowledge_field.mean(axis=0)))[:32]

