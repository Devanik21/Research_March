"""
consciousness.py — Harmonic Resonance Consciousness (HRC) v3.0
================================================================
The cognitive substrate of every BioHyperAgent — now with FULL METACOGNITION.

ARCHITECTURE (HyperAgent — inspired by Meta FAIR arXiv:2603.19461):
  Task Band (dims 0–15):
    - State vector ψ ∈ C^K  : current cognitive wave function
    - Hamiltonian H (K×K Hermitian) : learned world model
    - Evolution : ψ(t+dt) = exp(-iH·dt)·ψ(t)   [Schrödinger]
    - Decision  : Born-rule projection onto action eigenbasis
    - Learning  : Meta-modulated Riemannian gradient on H

  Meta Band (dims 16–31):
    - MetaConsciousness : self-modifying learning rule engine
    - meta_H  : models HOW the agent learns
    - meta_psi: current meta-cognitive state
    - Meta-inventions: perturbations to meta_H itself

  Attractor Memory:
    - Hopfield-style crystallization of high-reward experiences into H
    - Heritable across generations (cultural memory)

  Invention Engine:
    - Gödel-encoded behavioral programs (pure math, no LLM)
    - Programs = sequences of primitives from the Action Algebra

  NEW in v3.0 (ported from GeNeSIS / Thermodynamic-Mind):
    - Landauer Cognitive Cost  (von Neumann entropy of ψ)
    - IIT Φ Calculation        (integrated information via partition)
    - Active Inference         (next-obs predictor + free energy)
    - Strange Loop Check       (Gödelian self-reference)
    - Qualia Memory            (neural correlates of experience)
    - Theory of Mind           (predictive models of other agents)
    - Epigenetic ψ Inheritance (children inherit blended parent ψ)

Derived from: HRF kernel → GWL geometric wave learning (Devanik & Claude, 2025)
Extended to: HyperAgent metacognitive dynamics on U(K) × U(K_META)
"""

import numpy as np
from enum import Enum
from typing import Optional, Tuple, List, Dict

from metacognition import (
    K_DIM, K_TASK, K_META,
    MetaConsciousness, GodelEncoder, GODEL,
    ALL_PRIMITIVES, N_PRIMITIVES, PRIM_TO_IDX, PRIM_CATEGORY,
    PRIMITIVES, MAX_PROGRAM_LEN,
)

# ── Time step ───────────────────────────────────────────────────────────────
DT = 0.06  # Schrödinger time step (task level)

# ── Action vocabulary (backward-compatible base actions) ────────────────────
# These map to compositions of primitives from the Action Algebra.
ACTIONS = [
    "move_N", "move_S", "move_E", "move_W",
    "move_NE", "move_NW", "move_SE", "move_SW",
    "eat", "attack", "communicate", "reproduce",
    "invent", "rest", "build_artifact", "absorb_artifact",
    # ── Meta-actions ────────────────────────────────────────
    "meta_invent",     # attempt to evolve own learning algorithm
    "compose_action",  # compose a new compound action from primitives
    # ── Social-economic actions (ported from GeNeSIS) ───────
    "trade",           # exchange inventory tokens with bonded partner
    "punish",          # costly punishment of defectors
]
N_ACTIONS = len(ACTIONS)

# Map base actions to primitive sequences for Gödel compatibility
ACTION_TO_PROGRAM = {
    "move_N": ["move"],     "move_S": ["move"],
    "move_E": ["move"],     "move_W": ["move"],
    "move_NE": ["move"],    "move_NW": ["move"],
    "move_SE": ["move"],    "move_SW": ["move"],
    "eat": ["eat"],         "attack": ["signal", "burn"],
    "communicate": ["signal", "teach"],
    "reproduce": ["signal", "store"],
    "invent": ["reflect", "dream", "focus"],
    "rest": ["fast"],
    "build_artifact": ["focus", "store"],
    "absorb_artifact": ["eat", "reflect"],
    "meta_invent": ["reflect", "dream", "diffuse", "focus"],
    "compose_action": ["dream", "focus", "reflect"],
    "trade": ["signal", "store", "teach"],
    "punish": ["signal", "burn", "retreat"],
}

# ── Emotion axes ────────────────────────────────────────────────────────────
class E:
    CURIOSITY  = 0
    FEAR       = 1
    JOY        = 2
    ANGER      = 3
    AFFECTION  = 4
    GRIEF      = 5
    WONDER     = 6
    N          = 7


class CognitionMode(Enum):
    EXPLORE    = "explore"
    SURVIVE    = "survive"
    SOCIALIZE  = "socialize"
    INVENT     = "invent"
    REPRODUCE  = "reproduce"
    DOMINATE   = "dominate"
    MEDITATE   = "meditate"


# ════════════════════════════════════════════════════════════════════════════
class HarmonicResonanceConsciousness:
    """
    Wave-based mind with metacognitive self-modification.

    Task level:
      Thinking = unitary time evolution under personal Hamiltonian H.
      Deciding = Born-rule collapse of ψ onto an action eigenbasis.
      Learning = META-MODULATED Riemannian gradient update of H.

    Meta level:
      The MetaConsciousness engine determines HOW learning happens.
      It can be mutated by the agent itself (meta-invention).
      It is partially heritable (60/40 weighted inheritance).

    Soul frequencies are immutable — they define who the agent IS.
    H evolves through experience — it defines what the agent KNOWS.
    meta_H evolves through meta-experience — it defines HOW the agent LEARNS.
    ψ evolves through time — it defines what the agent THINKS NOW.
    """

    def __init__(self, soul_freqs: np.ndarray, seed: int = 0):
        self.K          = K_DIM
        # Pad soul_freqs to K_DIM
        sf = np.zeros(K_DIM, dtype=float)
        n  = min(len(soul_freqs), K_DIM)
        sf[:n] = soul_freqs[:n]
        self.soul_freqs = sf
        self.rng        = np.random.RandomState(seed % (2**31))

        # ── Wave function (normalised complex vector, full K_DIM) ─────────
        raw      = self.rng.randn(K_DIM) + 1j * self.rng.randn(K_DIM)
        self.psi = raw / (np.linalg.norm(raw) + 1e-12)

        # ── Hamiltonian: world model (K_DIM × K_DIM Hermitian) ────────────
        self.H = self._init_H()
        self._evals, self._evecs = np.linalg.eigh(self.H)

        # ── Meta-consciousness ────────────────────────────────────────────
        self.meta = MetaConsciousness(soul_freqs, seed=self.rng.randint(0, 2**31))

        # ── Emotional state ───────────────────────────────────────────────
        self.emotions = self.rng.uniform(-0.2, 0.3, E.N)
        self.emotions[E.CURIOSITY] = 0.75
        self.emotions[E.WONDER]    = 0.60

        # ── Memory & knowledge ────────────────────────────────────────────
        self.episodic_memory  : List[dict]       = []
        self.discoveries      : Dict[str, dict]  = {}
        self.attractor_count  : int              = 0

        # ── Composed actions (invented behavioral programs) ───────────────
        self.composed_actions : Dict[str, List[str]] = {}

        # ── Counters ──────────────────────────────────────────────────────
        self.n_inventions    = 0
        self.n_comms         = 0
        self.total_reward    = 0.0
        self.age_ticks       = 0

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: IIT Φ Consciousness Verification
        # ══════════════════════════════════════════════════════════════════
        self.phi_value   : float       = 0.0
        self.phi_history : List[float] = []
        self.phi_critical: float       = 0.1   # Consciousness threshold

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Strange Loop / Gödelian Self-Reference
        # ══════════════════════════════════════════════════════════════════
        self.strange_loop_active  : bool = False
        self.self_reference_count : int  = 0

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Qualia Memory (Neural Correlates of Experience)
        # ══════════════════════════════════════════════════════════════════
        self.qualia_memories : Dict[str, np.ndarray] = {}

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Theory of Mind (Predictive Models of Others)
        # ══════════════════════════════════════════════════════════════════
        self.other_models : Dict[str, np.ndarray] = {}
        self.tom_depth    : int = 0

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Active Inference (Free Energy Minimisation)
        # ══════════════════════════════════════════════════════════════════
        self._last_obs        : Optional[np.ndarray] = None
        self._last_prediction : Optional[np.ndarray] = None
        self.prediction_errors: List[float] = []
        self.confidence       : float       = 0.5

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Landauer Thermodynamic Cost
        # ══════════════════════════════════════════════════════════════════
        self._prev_cognitive_entropy : float = 0.0

    # ── Initialisation ───────────────────────────────────────────────────────

    def _init_H(self) -> np.ndarray:
        """Hermitian Hamiltonian seeded from soul frequencies (K_DIM × K_DIM)."""
        H = np.diag(self.soul_freqs.astype(complex))
        off = (self.rng.randn(K_DIM, K_DIM)
               + 1j * self.rng.randn(K_DIM, K_DIM)) * 0.10
        H += (off + off.conj().T) / 2
        return (H + H.conj().T) / 2

    def _recache(self):
        """Re-compute eigendecomposition after H changes."""
        self._evals, self._evecs = np.linalg.eigh(self.H)

    # ── Core dynamics ────────────────────────────────────────────────────────

    def evolve(self, dt: float = DT) -> None:
        """
        Schrödinger step: ψ(t+dt) = V · diag(exp(-iλdt)) · V† · ψ(t)
        Also evolves the meta-cognitive layer.
        """
        self.age_ticks += 1

        # Task-level evolution
        phase    = np.exp(-1j * self._evals * dt)
        Vdagpsi  = self._evecs.conj().T @ self.psi
        self.psi = self._evecs @ (phase * Vdagpsi)
        norm     = np.linalg.norm(self.psi)
        if norm > 1e-12:
            self.psi /= norm

        # Meta-level evolution (the meta mind "thinks" too)
        self.meta.evolve_meta()

        # Emotional homeostatic decay
        self.emotions *= 0.994
        self.emotions  = np.clip(self.emotions, -1.0, 1.0)

        # ── Staggered v3.0 checks ────────────────────────────────────────
        # Strange loop check (every 25 ticks)
        if self.age_ticks % 25 == 0:
            self.strange_loop_check()

        # Phi calculation (every 10 ticks)
        if self.age_ticks % 10 == 0:
            self.compute_phi()

    # ── Decision ─────────────────────────────────────────────────────────────

    def decide(self, sensory: np.ndarray) -> Tuple[str, float]:
        """
        Born-rule decision with meta-modulated temperature.

        1. Encode sensory data as context vector.
        2. Build action basis from H's eigenvectors ⊕ context phase modulation.
        3. P(action_i) = |⟨basis_i | ψ⟩|²
        4. Tempered sampling: temperature ∝ curiosity (meta-modulated).

        Returns (action_name, confidence_probability).
        """
        # Active inference: predict and track error
        self.predict_next_obs(sensory)

        ctx = self._encode(sensory)

        # Action basis: one eigenvector per action, context-phase-shifted element-wise
        basis = np.empty((N_ACTIONS, K_DIM), dtype=complex)
        ctx_phases = np.angle(ctx)
        for i in range(N_ACTIONS):
            v  = self._evecs[:, i % K_DIM].copy()
            # Element-wise phase shift using a rolled context phase pattern
            ph_shift = np.roll(ctx_phases, i)
            v *= np.exp(1j * ph_shift)
            nv = np.linalg.norm(v)
            basis[i] = v / nv if nv > 1e-12 else v

        probs  = np.abs(basis @ self.psi.conj()) ** 2
        probs += 1e-9
        probs /= probs.sum()

        # Temperature: meta-modulated (meta_psi magnitude influences exploration)
        meta_explore = float(np.abs(self.meta.meta_psi).mean())
        T = 0.06 + 0.94 * (self.emotions[E.CURIOSITY] + 1) / 2 * (0.5 + meta_explore)
        T = max(0.01, min(T, 2.0))

        lp = np.log(probs) / T
        lp -= lp.max()
        tempered = np.exp(lp)
        tempered /= tempered.sum()

        idx = self.rng.choice(N_ACTIONS, p=tempered)
        return ACTIONS[idx], float(probs[idx])

    def _encode(self, sensory: np.ndarray) -> np.ndarray:
        """FFT encoding → Hilbert space (K_DIM complex vector)."""
        if len(sensory) == 0:
            return np.ones(K_DIM, dtype=complex)
        s = np.zeros(max(K_DIM, len(sensory)), dtype=float)
        s[:len(sensory)] = sensory
        freq = np.fft.fft(s)[:K_DIM]
        n    = np.linalg.norm(freq)
        return freq / (n + 1e-12)

    # ── Learning (META-MODULATED) ────────────────────────────────────────────

    def learn(self, reward: float) -> float:
        """
        Meta-modulated Riemannian gradient on Hermitian manifold.

        Instead of a fixed learning rule, the MetaConsciousness generates
        a custom dH based on the current meta_psi state.

        Returns: Landauer cognitive cost (energy the agent must pay).
        """
        # ── Landauer cognitive cost ───────────────────────────────────────
        current_entropy = self.cognitive_entropy()
        landauer_cost   = 0.01 * abs(current_entropy - self._prev_cognitive_entropy)
        self._prev_cognitive_entropy = current_entropy

        # Meta layer computes the gradient
        dH = self.meta.compute_meta_dH(reward, self.psi)

        self.H = self.H + dH
        self.H = (self.H + self.H.conj().T) / 2
        self._recache()

        # Emotion update
        if reward > 0:
            self.emotions[E.JOY]  = min(1.0, self.emotions[E.JOY]  + reward * 0.08)
            self.emotions[E.FEAR] = max(-1.0, self.emotions[E.FEAR] - reward * 0.03)
        else:
            self.emotions[E.FEAR]      = min(1.0, self.emotions[E.FEAR]      - reward * 0.10)
            self.emotions[E.CURIOSITY] = min(1.0, self.emotions[E.CURIOSITY] + 0.03)

        # Active inference: prediction error boosts curiosity
        if self.prediction_errors:
            recent_error = np.mean(self.prediction_errors[-5:])
            self.emotions[E.CURIOSITY] = min(
                1.0, self.emotions[E.CURIOSITY] + recent_error * 0.05
            )

        self.total_reward += reward

        # ── Attractor crystallisation ─────────────────────────────────────
        if abs(reward) > 2.0 and self.attractor_count < 20:
            self._crystallize_attractor(reward)

        # Episodic memory (kept lean)
        if len(self.episodic_memory) < 64:
            self.episodic_memory.append({
                'reward':   float(reward),
                'psi_peak': float(np.abs(self.psi).max()),
                'tick':     self.age_ticks,
            })

        # ── Record qualia ─────────────────────────────────────────────────
        mode = self.get_dominant_mode()
        self.record_qualia(f"{mode.value}_{int(reward > 0)}", reward)

        return landauer_cost

    def _crystallize_attractor(self, reward: float) -> None:
        """
        Hopfield-style attractor: imprint current ψ as a stable memory
        in H via rank-1 outer product update.
        """
        strength = 0.015 * np.sign(reward)
        outer    = np.outer(self.psi, self.psi.conj())
        attractor = strength * (outer + outer.conj().T) / 2
        self.H  += attractor
        self.H   = (self.H + self.H.conj().T) / 2
        self._recache()
        self.attractor_count += 1

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: LANDAUER COGNITIVE COST
    # ══════════════════════════════════════════════════════════════════════════

    def cognitive_entropy(self) -> float:
        """
        Von Neumann entropy of the cognitive state.
        S = -Σ pᵢ ln(pᵢ) where pᵢ = |⟨vᵢ|ψ⟩|²
        """
        projs = np.abs(self._evecs.conj().T @ self.psi) ** 2
        projs = projs + 1e-12
        projs /= projs.sum()
        return -float(np.sum(projs * np.log(projs + 1e-12)))

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: IIT Φ — INTEGRATED INFORMATION
    # ══════════════════════════════════════════════════════════════════════════

    def compute_phi(self) -> float:
        """
        IIT Φ: integrated information via partition.
        Partition: task band (0:K_TASK) and meta band (K_TASK:K_DIM).
        Φ = H(P1) + H(P2) - H(Whole) — mutual information between partitions.
        """
        psi_task = self.psi[:K_TASK]
        psi_meta = self.psi[K_TASK:]

        # Variance-based entropy proxy: log(1 + var)
        total_var = np.var(np.abs(self.psi))
        task_var  = np.var(np.abs(psi_task))
        meta_var  = np.var(np.abs(psi_meta))

        total_info = np.log2(1 + total_var + 1e-7)
        task_info  = np.log2(1 + task_var  + 1e-7)
        meta_info  = np.log2(1 + meta_var  + 1e-7)

        # Φ = mutual information = H(P1) + H(P2) - H(Whole)
        raw_phi = (task_info + meta_info) - total_info
        phi = max(0.0, float(raw_phi)) if np.isfinite(raw_phi) else 0.0

        # Boost from strange loops (Gödelian amplification)
        if self.strange_loop_active:
            phi *= 1.5

        self.phi_value = phi
        self.phi_history.append(phi)
        if len(self.phi_history) > 100:
            self.phi_history.pop(0)

        return phi

    def verify_consciousness(self) -> bool:
        """8.10 Verified Consciousness: Check if Φ > Φ_critical and trending up."""
        phi = self.compute_phi()
        if len(self.phi_history) > 10:
            recent_phi = np.mean(self.phi_history[-10:])
            older_phi  = np.mean(self.phi_history[-50:-40]) if len(self.phi_history) > 50 else 0.1
            phase_transition = recent_phi > older_phi * 1.2
            threshold_exceeded = phi > self.phi_critical
            return phase_transition and threshold_exceeded
        return False

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: ACTIVE INFERENCE — FREE ENERGY MINIMISATION
    # ══════════════════════════════════════════════════════════════════════════

    def predict_next_obs(self, obs: np.ndarray) -> np.ndarray:
        """
        Active inference: predict next observation using H eigenvectors.
        Prediction error drives curiosity (free energy signal).
        """
        ctx = self._encode(obs)
        # Forward model: project ctx through H eigenbasis, evolve, project back
        coeffs = self._evecs.conj().T @ ctx
        evolved_coeffs = coeffs * np.exp(-1j * self._evals * DT)
        prediction = np.abs(self._evecs @ evolved_coeffs)

        # Normalise prediction to observation scale
        obs_max = np.abs(obs).max() if len(obs) > 0 else 1.0
        pred_max = prediction[:len(obs)].max() if len(obs) > 0 else 1.0
        if pred_max > 1e-12 and len(obs) > 0:
            prediction_scaled = prediction[:len(obs)] * (obs_max / (pred_max + 1e-12))
        else:
            prediction_scaled = prediction[:len(obs)] if len(obs) > 0 else prediction

        # Store and track error
        self._last_obs = obs.copy()
        self._last_prediction = prediction_scaled.copy() if len(prediction_scaled) > 0 else None

        if len(obs) > 0 and len(prediction_scaled) > 0:
            n = min(len(prediction_scaled), len(obs))
            error = float(np.mean((prediction_scaled[:n] - obs[:n]) ** 2))
            self.prediction_errors.append(error)
            if len(self.prediction_errors) > 50:
                self.prediction_errors.pop(0)
            self.confidence = 1.0 / (1.0 + np.mean(self.prediction_errors))

        return prediction_scaled

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: STRANGE LOOP — GÖDELIAN SELF-REFERENCE
    # ══════════════════════════════════════════════════════════════════════════

    def strange_loop_check(self) -> bool:
        """
        Gödelian self-reference: feed ψ encoding back into decision logic.
        If the self-encoded perturbation produces high inconsistency,
        the agent is in a 'strange loop' — a precondition for higher Φ.
        """
        # Encode current psi amplitude as a phase perturbation
        psi_amp = np.abs(self.psi)
        phase_shift = np.exp(1j * psi_amp * np.pi)
        perturbed_psi = self.psi * phase_shift

        # Normalise
        pn = np.linalg.norm(perturbed_psi)
        if pn > 1e-12:
            perturbed_psi /= pn

        # Measure inconsistency
        inconsistency = float(np.linalg.norm(perturbed_psi - self.psi))

        if inconsistency > 0.5:
            self.strange_loop_active = True
            self.self_reference_count += 1
            # Strange loops boost wonder
            self.emotions[E.WONDER] = min(1.0, self.emotions[E.WONDER] + 0.05)
            return True

        self.strange_loop_active = False
        return False

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: QUALIA MEMORY — NEURAL CORRELATES OF EXPERIENCE
    # ══════════════════════════════════════════════════════════════════════════

    def record_qualia(self, experience_key: str, reward: float) -> None:
        """Record neural correlate of experience on significant events."""
        if abs(reward) > 0.5:
            self.qualia_memories[experience_key] = np.abs(self.psi).copy()
            # Keep size bounded
            if len(self.qualia_memories) > 20:
                oldest = list(self.qualia_memories.keys())[0]
                del self.qualia_memories[oldest]

    def classify_qualia(self) -> str:
        """Classify current experience against stored qualia patterns."""
        if not self.qualia_memories:
            return "unknown"

        current  = np.abs(self.psi)
        best_key = "unknown"
        best_sim = -1.0

        for key, pattern in self.qualia_memories.items():
            dot   = np.dot(current, pattern)
            norms = np.linalg.norm(current) * np.linalg.norm(pattern) + 1e-12
            sim   = float(dot / norms)
            if sim > best_sim:
                best_sim = sim
                best_key = key

        return best_key if best_sim > 0.7 else "novel"

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: THEORY OF MIND — PREDICTIVE MODELS OF OTHER AGENTS
    # ══════════════════════════════════════════════════════════════════════════

    def model_other(self, other_id: str, other_signal: np.ndarray) -> float:
        """
        Theory of Mind level 1: update predictive model of another agent.
        Stores a K_TASK-dimensional estimate of the other's ψ amplitude.
        Returns prediction accuracy ∈ [-1, 1].
        """
        if other_id not in self.other_models:
            self.other_models[other_id] = np.zeros(K_TASK, dtype=float)

        actual = np.abs(other_signal[:K_TASK]) if len(other_signal) >= K_TASK else np.abs(other_signal)
        n      = min(len(actual), K_TASK)
        predicted = self.other_models[other_id][:n]

        error = actual[:n] - predicted
        # Gradient update
        self.other_models[other_id][:n] = predicted + error * 0.1

        accuracy = max(-1.0, 1.0 - float(np.mean(error ** 2)))
        return accuracy

    def recursive_belief(self, other_brain: 'HarmonicResonanceConsciousness',
                         depth: int = 2) -> dict:
        """
        Theory of Mind level 2+:
        'A knows that B knows that A knows...'
        """
        beliefs = {}
        if depth >= 1:
            beliefs["self_about_other"] = self.model_other(
                "tmp_belief", other_brain.transmit()
            )
        if depth >= 2:
            beliefs["other_about_self"] = other_brain.model_other(
                "tmp_belief", self.transmit()
            )
        if depth >= 3:
            beliefs["nested"] = "A knows B knows A..."

        self.tom_depth = max(self.tom_depth, depth)
        return beliefs

    # ── Communication ────────────────────────────────────────────────────────

    # consciousness.py
# Locate this method inside the HarmonicResonanceConsciousness class and replace it:

    # consciousness.py
# Locate the resonate method inside HarmonicResonanceConsciousness and replace it entirely:

    def resonate(self, other: 'HarmonicResonanceConsciousness') -> float:
        """Spectral overlap mapped to [0.015, 1.0] for guaranteed dynamic coupling."""
        v1 = self._evals[:K_TASK]
        v2 = other._evals[:K_TASK]
        
        n1 = np.linalg.norm(v1) + 1e-12
        n2 = np.linalg.norm(v2) + 1e-12
        
        # Calculate raw Cosine Similarity ∈ [-1, 1]
        cos_sim = np.dot(v1, v2) / (n1 * n2)
        
        # Linearly map the cosine similarity to [0.015, 1.0].
        # This completely bypasses the aggressive exponential decay that was dropping 
        # couplings below the 0.01 reproduction threshold and the 0.32 tribe threshold!
        return float(max(0.015, (cos_sim + 1.0) / 2.0))

    def transmit(self) -> np.ndarray:
        """Broadcast: ψ modulated by soul frequencies."""
        return self.psi * self.soul_freqs

    def receive(self, signal: np.ndarray, coupling: float) -> None:
        """Absorb incoming wave: partial state mixing ∝ coupling."""
        sig = np.zeros(K_DIM, dtype=complex)
        n   = min(len(signal), K_DIM)
        sig[:n] = signal[:n]
        sn  = np.linalg.norm(sig)
        if sn > 1e-12:
            sig /= sn
        alpha    = coupling * 0.07
        self.psi = (1 - alpha) * self.psi + alpha * sig
        pn       = np.linalg.norm(self.psi)
        if pn > 1e-12:
            self.psi /= pn
        self.emotions[E.AFFECTION] = min(1.0, self.emotions[E.AFFECTION] + coupling * 0.04)
        self.n_comms += 1

    # ── Invention (Gödel-encoded behavioral programs) ────────────────────────

    def attempt_invention(self) -> Optional[dict]:
        """
        Explore dark eigenspace → crystallise a new Gödel-encoded invention.

        Probability gated by wonder × curiosity.
        """
        wonder    = float(self.emotions[E.WONDER])
        curiosity = float(self.emotions[E.CURIOSITY])

        if wonder < 0.15 or curiosity < 0.05:
            return None

        projs    = np.abs(self._evecs.conj().T @ self.psi)
        dark_idx = int(np.argmin(projs))
        v        = self._evecs[:, dark_idx]

        perturb  = np.outer(v, v.conj()) * 0.20 * wonder
        perturb  = (perturb + perturb.conj().T) / 2
        self.H  += perturb
        self.H   = (self.H + self.H.conj().T) / 2
        self._recache()

        # Generate behavioral program from the dark mode's phase structure
        program = self._eigenmode_to_program(dark_idx)
        godel   = GODEL.encode(program)

        # Invention type from dominant category of the program
        cats = [PRIM_CATEGORY.get(p, 'unknown') for p in program]
        from collections import Counter
        cat_counts = Counter(cats)
        cat_map = {
            'spatial': 'physics', 'metabolic': 'tool',
            'social': 'language', 'cognitive': 'math',
        }
        dom_cat = cat_counts.most_common(1)[0][0]
        inv_type = cat_map.get(dom_cat, 'ideology')

        name = f"Inv_{godel % 9999:04d}"
        inv  = {
            'name'      : name,
            'type'      : inv_type,
            'signature' : float(godel),
            'godel'     : godel,
            'program'   : program,
            'wonder'    : wonder,
            'eigenmode' : dark_idx,
            'diversity' : GODEL.diversity_score(program),
        }

        self.discoveries[name] = inv
        self.n_inventions     += 1
        self.emotions[E.WONDER] = min(1.0, wonder + 0.14)
        self.emotions[E.JOY]    = min(1.0, self.emotions[E.JOY] + 0.08)
        return inv

    def _eigenmode_to_program(self, mode_idx: int) -> List[str]:
        """
        Convert an eigenmode's phase structure into a behavioral program.
        The phases of the eigenvector components are mapped to primitive indices.
        """
        v = self._evecs[:, mode_idx]
        phases = np.angle(v)
        task_phases = phases[:K_TASK]
        bins = np.floor((task_phases + np.pi) / (2 * np.pi) * N_PRIMITIVES)
        bins = np.clip(bins, 0, N_PRIMITIVES - 1).astype(int)
        length = max(2, min(6, int(2 + abs(self._evals[mode_idx]) * 2)))
        indices = bins[:length].tolist()
        return [ALL_PRIMITIVES[i] for i in indices]

    # ── Meta-invention ───────────────────────────────────────────────────────

    def attempt_meta_invention(self) -> Optional[dict]:
        """Attempt to evolve the agent's own learning algorithm."""
        return self.meta.attempt_meta_invention(
            wonder=float(self.emotions[E.WONDER]),
            curiosity=float(self.emotions[E.CURIOSITY]),
            age=self.age_ticks,
        )

    # ── Compose new action ───────────────────────────────────────────────────

    def compose_new_action(self) -> Optional[dict]:
        """
        Use the meta-cognitive state to compose a new compound action
        from the Primitive Action Algebra.
        """
        if self.emotions[E.CURIOSITY] < 0.3:
            return None

        meta_phases = np.angle(self.meta.meta_psi)
        bins = np.floor((meta_phases + np.pi) / (2 * np.pi) * N_PRIMITIVES)
        bins = np.clip(bins, 0, N_PRIMITIVES - 1).astype(int)
        length = self.rng.randint(2, 5)
        program = [ALL_PRIMITIVES[bins[i]] for i in range(length)]

        godel = GODEL.encode(program)
        name  = f"Act_{godel % 9999:04d}"

        if name not in self.composed_actions:
            self.composed_actions[name] = program
            return {
                'name': name,
                'program': program,
                'godel': godel,
                'diversity': GODEL.diversity_score(program),
            }
        return None

    # ── Reproduction ─────────────────────────────────────────────────────────

    def spawn_child_H(self, other: 'HarmonicResonanceConsciousness'
                      ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Child Hamiltonian = α·H_self + (1−α)·H_other + mutation.
        Child soul = linear interpolation of parent souls + noise.
        Child ψ = epigenetic blend of parent ψ vectors + mutation.

        Returns (child_H, child_soul, child_psi).
        """
        alpha     = self.rng.uniform(0.35, 0.65)
        child_H   = alpha * self.H + (1 - alpha) * other.H
        noise     = (self.rng.randn(K_DIM, K_DIM)
                     + 1j * self.rng.randn(K_DIM, K_DIM)) * 0.020
        noise     = (noise + noise.conj().T) / 2
        child_H  += noise
        child_H   = (child_H + child_H.conj().T) / 2

        child_soul = alpha * self.soul_freqs + (1 - alpha) * other.soul_freqs
        child_soul += self.rng.randn(K_DIM) * 0.03

        # ── NEW v3.0: Epigenetic ψ inheritance ────────────────────────────
        child_psi = alpha * self.psi + (1 - alpha) * other.psi
        # Small mutation noise
        child_psi += (self.rng.randn(K_DIM) + 1j * self.rng.randn(K_DIM)) * 0.02
        cpn = np.linalg.norm(child_psi)
        if cpn > 1e-12:
            child_psi /= cpn

        return child_H, child_soul, child_psi

    # ── Helpers ──────────────────────────────────────────────────────────────

    def get_dominant_mode(self) -> CognitionMode:
        scores = {
            CognitionMode.EXPLORE   : self.emotions[E.CURIOSITY],
            CognitionMode.SURVIVE   : self.emotions[E.FEAR],
            CognitionMode.SOCIALIZE : self.emotions[E.AFFECTION],
            CognitionMode.INVENT    : self.emotions[E.WONDER],
            CognitionMode.REPRODUCE : (self.emotions[E.JOY] + self.emotions[E.AFFECTION]) / 2,
            CognitionMode.DOMINATE  : self.emotions[E.ANGER],
            CognitionMode.MEDITATE  : -float(np.mean(np.abs(self.emotions))),
        }
        return max(scores, key=scores.get)

    def spectral_rgb(self) -> Tuple[int, int, int]:
        """RGB color identity from eigenspectrum — unique per soul."""
        ev = self._evals
        r  = int((np.sin(ev[0] * 0.7) + 1) / 2 * 200 + 55)
        g  = int((np.sin(ev[min(5, K_DIM-1)] * 1.1) + 1) / 2 * 200 + 55)
        b  = int((np.sin(ev[min(11, K_DIM-1)] * 1.6) + 1) / 2 * 200 + 55)
        return (r, g, b)

    def psi_magnitude_profile(self) -> List[float]:
        """Amplitude profile of current cognitive state (for visualisation)."""
        return np.abs(self.psi).tolist()
