"""
agents.py — BioHyperAgent
==========================
A truly bio-inspired living organism.

SOUL    : Immutable spectral frequency signature  (eigenfrequency identity)
BRAIN   : HarmonicResonanceConsciousness          (wave-based cognition)
BODY    : Physical presence, energy metabolism, health, aging
WILL    : Autonomous action selection — no external task, no reward shaping
DEATH   : Finite lifespan; leaves legacy artifact

Actions available: move (8 dirs), eat, attack, communicate, reproduce,
                   invent, rest, build_artifact, absorb_artifact.

All 128 agents are seeded with distinct soul frequencies → genuinely
diverse personalities emerging from spectral identity differences.

Invented by Devanik & Claude (Xylia) — Event Horizon Project
"""

import numpy as np
import uuid
from typing import Optional, List, Dict, Tuple

from consciousness import (
    HarmonicResonanceConsciousness, CognitionMode,
    ACTIONS, K_DIM, E
)

# ── Physics constants ────────────────────────────────────────────────────────
_BASE_FREQS = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 11.0,
                         13.0, 17.0, 19.0, 23.0, 29.0, 31.0])  # first 12 primes


class BioHyperAgent:
    """
    One living organism inside the Spectral Life simulation.

    Lifecycle:
        spawn → live (sense → decide → act → learn → evolve) → die → legacy

    Social dynamics emerge from resonance coupling between agents.
    Technology propagates via artifact placement and absorption.
    Civilisations form when resonance-compatible agents cluster.
    """

    # ── Life constants ───────────────────────────────────────────────────────
    MAX_AGE           = 480
    BASE_METABOLISM   = 0.07    # energy/tick
    MOVE_COST         = 0.04
    ATTACK_COST       = 0.18
    REPRODUCE_COST    = 1.6
    INVENT_COST       = 0.85
    BUILD_COST        = 0.90
    COMMUNICATE_COST  = 0.03

    def __init__(
        self,
        agent_id      : Optional[str] = None,
        x             : int  = 0,
        y             : int  = 0,
        world_size    : int  = 60,
        seed          : int  = None,
        parent_ids    : Optional[List[str]] = None,
        generation    : int  = 0,
    ):
        self.id           = agent_id or str(uuid.uuid4())[:8]
        self.x            = int(x)
        self.y            = int(y)
        self.world_size   = world_size
        self.parent_ids   = parent_ids or []
        self.generation   = generation
        self.rng          = np.random.RandomState((seed or np.random.randint(0, 2**30)) % (2**31))

        # ── Soul (immutable) ─────────────────────────────────────────────
        self.soul_freqs = self._forge_soul()

        # ── Brain ────────────────────────────────────────────────────────
        self.brain = HarmonicResonanceConsciousness(
            self.soul_freqs, seed=self.rng.randint(0, 2**31)
        )

        # ── Body ─────────────────────────────────────────────────────────
        self.energy   = 4.5
        self.health   = 1.0
        self.age      = 0
        self.alive    = True

        # ── Social ──────────────────────────────────────────────────────
        self.tribe_id        : Optional[str] = None
        self.reputation      : float         = 0.0
        self.n_kills         : int           = 0
        self.n_children      : int           = 0

        # ── Action state ─────────────────────────────────────────────────
        self.last_action         : str  = "born"
        self.last_action_success : bool = True
        self.action_counts       : Dict[str, int] = {}

        # ── Knowledge ────────────────────────────────────────────────────
        self.tools               : List[str] = []
        self.absorbed_inventions : List[str] = []

    # ── Soul generation ──────────────────────────────────────────────────────

    def _forge_soul(self) -> np.ndarray:
        """
        Soul = unique combination of prime-harmonic base frequencies
        modulated by random phases and amplitudes.
        Every agent has a truly unique spectral fingerprint.
        """
        phases     = self.rng.uniform(0, 2 * np.pi, K_DIM)
        amplitudes = self.rng.exponential(1.0, K_DIM) + 0.1
        return _BASE_FREQS * np.cos(phases) * amplitudes

    # ── Perception ───────────────────────────────────────────────────────────

    def sense(self, world) -> np.ndarray:
        """
        Build sensory observation vector:
        local resource gradients + own state + social density.
        """
        obs = []

        # Local resource field (sparse 5×5 sample)
        for dx in (-4, -2, 0, 2, 4):
            for dy in (-4, -2, 0, 2, 4):
                nx = (self.x + dx) % self.world_size
                ny = (self.y + dy) % self.world_size
                obs.extend(world.resources[nx, ny].tolist())

        # Own vitals
        obs += [
            self.energy / 10.0,
            self.health,
            self.age / self.MAX_AGE,
            self.reputation / 10.0,
            len(self.brain.discoveries) / 20.0,
        ]

        # Social density (nearby alive agents)
        nearby_count = len(world.get_agents_near(self.x, self.y, radius=5))
        obs.append(nearby_count / 15.0)

        return np.array(obs, dtype=float)

    # ── Main step ────────────────────────────────────────────────────────────

    def step(self, world, all_agents: Dict[str, 'BioHyperAgent']
             ) -> Optional['BioHyperAgent']:
        """
        One life tick.
        Returns a child BioHyperAgent if reproduction occurs, else None.
        """
        if not self.alive:
            return None

        self.age    += 1
        self.energy -= self.BASE_METABOLISM

        # Sensory input
        sensory = self.sense(world)

        # Decide (Born-rule quantum decision)
        action, confidence = self.brain.decide(sensory)

        # Cognitive-mode bias (40% chance to override toward dominant mode)
        action = self._mode_bias(action)

        # Execute and collect reward
        reward, child = self._execute(action, world, all_agents)

        # Learn from outcome
        self.brain.learn(reward)
        self.brain.evolve()

        # Log
        self.last_action         = action
        self.last_action_success = (reward >= 0)
        self.action_counts[action] = self.action_counts.get(action, 0) + 1

        # Death check
        if self.energy <= 0 or self.health <= 0 or self.age >= self.MAX_AGE:
            self.die(world)

        return child

    # ── Mode biasing ─────────────────────────────────────────────────────────

    def _mode_bias(self, base: str) -> str:
        BIAS = {
            CognitionMode.EXPLORE   : ["move_N","move_S","move_E","move_W",
                                        "move_NE","move_NW","move_SE","move_SW"],
            CognitionMode.SURVIVE   : ["eat","rest"],
            CognitionMode.SOCIALIZE : ["communicate","rest"],
            CognitionMode.INVENT    : ["invent","absorb_artifact","rest"],
            CognitionMode.REPRODUCE : ["reproduce","communicate"],
            CognitionMode.DOMINATE  : ["attack","move_N","move_S","move_E","move_W"],
            CognitionMode.MEDITATE  : ["rest","invent"],
        }
        mode    = self.brain.get_dominant_mode()
        options = BIAS.get(mode, [])
        if options and self.rng.random() < 0.38:
            return self.rng.choice(options)
        return base

    # ── Action dispatch ──────────────────────────────────────────────────────

    def _execute(self, action: str, world, all_agents: Dict
                 ) -> Tuple[float, Optional['BioHyperAgent']]:
        child = None
        try:
            if   action.startswith("move_"):   reward = self._move(action, world)
            elif action == "eat":              reward = self._eat(world)
            elif action == "attack":           reward = self._attack(world, all_agents)
            elif action == "communicate":      reward = self._communicate(world, all_agents)
            elif action == "reproduce":        reward, child = self._reproduce(world, all_agents)
            elif action == "invent":           reward = self._invent(world)
            elif action == "rest":             reward = self._rest()
            elif action == "build_artifact":   reward = self._build_artifact(world)
            elif action == "absorb_artifact":  reward = self._absorb_artifact(world)
            else:                              reward = 0.0
        except Exception:
            reward = -0.05
        return reward, child

    # ── Individual actions ────────────────────────────────────────────────────

    _DIR = {
        "move_N": (0,-1), "move_S": (0,1), "move_E": (1,0), "move_W": (-1,0),
        "move_NE":(1,-1), "move_NW":(-1,-1),"move_SE":(1,1), "move_SW":(-1,1),
    }

    def _move(self, direction: str, world) -> float:
        dx, dy   = self._DIR[direction]
        self.x   = (self.x + dx) % self.world_size
        self.y   = (self.y + dy) % self.world_size
        self.energy -= self.MOVE_COST
        local_res    = float(world.resources[self.x, self.y].sum())
        # Artifact bonus (knowledge-seekers gravitate toward artifacts)
        art_bonus = 0.1 if world.get_artifact(self.x, self.y) else 0.0
        return local_res * 0.04 - 0.01 + art_bonus

    def _eat(self, world) -> float:
        eaten = 0.0
        for r_type in range(2):   # food=0, energy_crystal=1
            consumed = world.consume_resource(self.x, self.y, r_type, 0.55)
            eaten   += consumed
        gain        = eaten * 0.85
        self.energy = min(10.0, self.energy + gain)
        self.health = min(1.0,  self.health + eaten * 0.04)
        return gain - 0.04

    def _attack(self, world, all_agents: Dict) -> float:
        nearby = [a for a in world.get_agents_near(self.x, self.y, radius=2)
                  if a.id != self.id and a.alive]
        if not nearby:
            self.energy -= 0.06
            return -0.12

        self.energy -= self.ATTACK_COST
        target       = self.rng.choice(nearby)
        damage       = 0.13 + self.rng.random() * 0.09

        target.health -= damage
        target.brain.emotions[E.FEAR]  = min(1.0, target.brain.emotions[E.FEAR]  + 0.35)
        target.brain.emotions[E.ANGER] = min(1.0, target.brain.emotions[E.ANGER] + 0.20)

        if target.health <= 0:
            target.alive = False
            target.die(world)
            self.n_kills   += 1
            self.reputation -= 1.2
            loot = target.energy * 0.45
            self.energy = min(10.0, self.energy + loot)
            self.brain.emotions[E.ANGER] = min(1.0, self.brain.emotions[E.ANGER] + 0.15)
            return 0.55

        self.reputation -= 0.25
        return 0.05

    def _communicate(self, world, all_agents: Dict) -> float:
        nearby = [a for a in world.get_agents_near(self.x, self.y, radius=5)
                  if a.id != self.id and a.alive]
        if not nearby:
            return -0.02
        self.energy -= self.COMMUNICATE_COST

        # Find most resonant partner
        partner  = max(nearby[:8], key=lambda a: self.brain.resonate(a.brain))
        coupling = self.brain.resonate(partner.brain)

        # Bidirectional wave exchange
        self.brain.receive(partner.brain.transmit(), coupling)
        partner.brain.receive(self.brain.transmit(), coupling)

        # Knowledge diffusion — share one random discovery
        if self.brain.discoveries:
            disc = self.rng.choice(list(self.brain.discoveries.values()))
            if disc['name'] not in partner.absorbed_inventions:
                partner.absorbed_inventions.append(disc['name'])
                partner.brain.emotions[E.WONDER] = min(
                    1.0, partner.brain.emotions[E.WONDER] + 0.06
                )

        if coupling > 0.45:
            self.reputation      += 0.08
            partner.reputation   += 0.08

        return coupling * 0.28 - 0.02

    def _reproduce(self, world, all_agents: Dict
                   ) -> Tuple[float, Optional['BioHyperAgent']]:
        if self.energy < self.REPRODUCE_COST:
            return -0.08, None

        nearby = [a for a in world.get_agents_near(self.x, self.y, radius=4)
                  if a.id != self.id and a.alive and a.energy > 1.2]
        if not nearby:
            return -0.05, None

        partner  = max(nearby, key=lambda a: self.brain.resonate(a.brain))
        coupling = self.brain.resonate(partner.brain)
        if coupling < 0.08:
            return -0.04, None

        self.energy      -= self.REPRODUCE_COST
        partner.energy   -= self.REPRODUCE_COST * 0.45

        child_H, child_soul = self.brain.spawn_child_H(partner.brain)

        cx = (self.x + self.rng.randint(-2, 3)) % self.world_size
        cy = (self.y + self.rng.randint(-2, 3)) % self.world_size

        child = BioHyperAgent(
            x=cx, y=cy,
            world_size=self.world_size,
            seed=self.rng.randint(0, 2**31),
            parent_ids=[self.id, partner.id],
            generation=max(self.generation, partner.generation) + 1,
        )
        child.soul_freqs = child_soul
        child.brain      = HarmonicResonanceConsciousness(
            child_soul, seed=self.rng.randint(0, 2**31)
        )
        child.brain.H    = child_H
        child.brain._recache()
        child.energy     = 2.2

        # Inherit up to 2 discoveries
        for name, disc in list(self.brain.discoveries.items())[:2]:
            child.brain.discoveries[name] = disc
            child.absorbed_inventions.append(name)

        self.n_children  += 1
        self.brain.emotions[E.JOY] = min(1.0, self.brain.emotions[E.JOY] + 0.28)
        return coupling * 0.45, child

    def _invent(self, world) -> float:
        if self.energy < self.INVENT_COST:
            return -0.06
        self.energy -= self.INVENT_COST
        inv = self.brain.attempt_invention()
        if inv is None:
            return -0.12
        world.place_artifact(self.x, self.y, {
            **inv,
            'creator'  : self.id,
            'step'     : world.step_count,
        })
        return 0.85

    def _rest(self) -> float:
        gain        = 0.22
        self.energy = min(10.0, self.energy + gain)
        self.health = min(1.0,  self.health + 0.018)
        self.brain.emotions *= 0.97   # calm down
        return 0.04

    def _build_artifact(self, world) -> float:
        if self.energy < self.BUILD_COST:
            return -0.08
        res = world.resources[self.x, self.y].sum()
        if res < 0.4:
            return -0.05
        self.energy -= self.BUILD_COST
        consumed = world.consume_resource(self.x, self.y, 3, 0.25)
        name     = f"Tool_{self.id}_{self.age}"
        world.place_artifact(self.x, self.y, {
            'name'      : name,
            'type'      : 'tool',
            'creator'   : self.id,
            'step'      : world.step_count,
            'signature' : float(consumed * 1000),
            'wonder'    : 0.0,
        })
        self.tools.append(name)
        return 0.30

    def _absorb_artifact(self, world) -> float:
        art = world.get_artifact(self.x, self.y)
        if art is None or art.get('creator') == self.id:
            return -0.02
        if art['name'] not in self.absorbed_inventions:
            self.absorbed_inventions.append(art['name'])
            self.brain.emotions[E.WONDER]    = min(1.0, self.brain.emotions[E.WONDER]    + 0.10)
            self.brain.emotions[E.CURIOSITY] = min(1.0, self.brain.emotions[E.CURIOSITY] + 0.05)
            return 0.42
        return 0.01

    # ── Death ────────────────────────────────────────────────────────────────

    def die(self, world) -> None:
        self.alive = False
        if self.brain.discoveries:
            legacy = list(self.brain.discoveries.values())[-1]
            world.place_artifact(self.x, self.y, {
                **legacy,
                'creator'  : self.id,
                'type'     : 'legacy',
                'step'     : world.step_count,
            })

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        rgb = self.brain.spectral_rgb()
        return {
            'id'          : self.id,
            'x'           : self.x,
            'y'           : self.y,
            'energy'      : round(float(self.energy), 2),
            'health'      : round(float(self.health), 3),
            'age'         : int(self.age),
            'alive'       : self.alive,
            'generation'  : self.generation,
            'tribe'       : self.tribe_id or 'Nomad',
            'mode'        : self.brain.get_dominant_mode().value,
            'last_action' : self.last_action,
            'reputation'  : round(float(self.reputation), 2),
            'inventions'  : len(self.brain.discoveries),
            'absorbed'    : len(self.absorbed_inventions),
            'kills'       : self.n_kills,
            'children'    : self.n_children,
            'color'       : f'rgb({rgb[0]},{rgb[1]},{rgb[2]})',
            'r'           : rgb[0],
            'g'           : rgb[1],
            'b'           : rgb[2],
            'curiosity'   : round(float(self.brain.emotions[E.CURIOSITY]), 2),
            'wonder'      : round(float(self.brain.emotions[E.WONDER]), 2),
            'fear'        : round(float(self.brain.emotions[E.FEAR]), 2),
        }
