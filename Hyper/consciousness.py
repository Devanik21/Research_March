"""
consciousness.py — Harmonic Resonance Consciousness (HRC)
==========================================================
The cognitive substrate of every BioHyperAgent.

ARCHITECTURE (novel — no prior art):
  - State vector ψ ∈ C^K  : current cognitive wave function
  - Hamiltonian H (K×K Hermitian) : learned world model
  - Evolution : ψ(t+dt) = exp(-iH·dt)·ψ(t)   [Schrödinger]
  - Decision  : Born-rule projection onto action eigenbasis
  - Learning  : Hermitian manifold gradient on H
  - Memory    : persistent resonance modes in H's eigenspectrum
  - Invention : eigenspace exploration of H's dark modes
  - Communication : wave field broadcast + resonance coupling

Derived from: HRF kernel → GWL geometric wave learning (Devanik & Claude, 2025)
Extended to: living cognitive dynamics operating on Unitary group U(K)
"""

import numpy as np
from enum import Enum
from typing import Optional, Tuple, List, Dict

# ── Global constants ────────────────────────────────────────────────────────
K_DIM = 12   # Hilbert space dimension per agent  (balance: richness vs speed)
DT    = 0.06  # Schrödinger time step

# ── Action vocabulary ───────────────────────────────────────────────────────
ACTIONS = [
    "move_N", "move_S", "move_E", "move_W",
    "move_NE", "move_NW", "move_SE", "move_SW",
    "eat", "attack", "communicate", "reproduce",
    "invent", "rest", "build_artifact", "absorb_artifact",
]
N_ACTIONS = len(ACTIONS)

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
    Wave-based mind. Not a neural network. Not an LLM. Not a decision tree.

    Each agent inhabits its own Hilbert space C^K.
    Thinking = unitary time evolution under personal Hamiltonian H.
    Deciding = Born-rule collapse of ψ onto an action eigenbasis.
    Learning = Riemannian gradient update of H on Hermitian manifold.
    Inventing = perturbation into least-explored eigenspace of H.
    Speaking  = broadcast of ψ modulated by soul frequencies.
    Listening = partial state mixing weighted by spectral overlap.

    Soul frequencies are immutable — they define who the agent IS.
    H evolves through experience — it defines what the agent KNOWS.
    ψ evolves through time — it defines what the agent THINKS NOW.
    """

    def __init__(self, soul_freqs: np.ndarray, seed: int = 0):
        self.K         = K_DIM
        self.soul_freqs = np.array(soul_freqs[:K_DIM], dtype=float)
        self.rng       = np.random.RandomState(seed % (2**31))

        # ── Wave function (normalised complex vector) ─────────────────────
        raw      = self.rng.randn(K_DIM) + 1j * self.rng.randn(K_DIM)
        self.psi = raw / (np.linalg.norm(raw) + 1e-12)

        # ── Hamiltonian: world model ───────────────────────────────────────
        self.H = self._init_H()
        self._evals, self._evecs = np.linalg.eigh(self.H)   # cached eig

        # ── Emotional state ────────────────────────────────────────────────
        self.emotions = self.rng.uniform(-0.2, 0.3, E.N)
        self.emotions[E.CURIOSITY] =  0.75
        self.emotions[E.WONDER]    =  0.60

        # ── Memory & knowledge ────────────────────────────────────────────
        self.episodic_memory : List[dict] = []
        self.discoveries     : Dict[str, dict] = {}

        # ── Counters ──────────────────────────────────────────────────────
        self.n_inventions    = 0
        self.n_comms         = 0
        self.total_reward    = 0.0
        self.age_ticks       = 0

    # ── Initialisation ───────────────────────────────────────────────────────

    def _init_H(self) -> np.ndarray:
        """Hermitian Hamiltonian seeded from soul frequencies."""
        H = np.diag(self.soul_freqs.astype(complex))
        off = (self.rng.randn(K_DIM, K_DIM) + 1j * self.rng.randn(K_DIM, K_DIM)) * 0.12
        H  += (off + off.conj().T) / 2
        return (H + H.conj().T) / 2

    def _recache(self):
        """Re-compute eigendecomposition after H changes."""
        self._evals, self._evecs = np.linalg.eigh(self.H)

    # ── Core dynamics ────────────────────────────────────────────────────────

    def evolve(self, dt: float = DT) -> None:
        """
        Schrödinger step: ψ(t+dt) = V · diag(exp(-iλdt)) · V† · ψ(t)
        O(K²) — fast for K=12.
        """
        self.age_ticks += 1
        phase     = np.exp(-1j * self._evals * dt)
        Vdagpsi   = self._evecs.conj().T @ self.psi
        self.psi  = self._evecs @ (phase * Vdagpsi)
        norm      = np.linalg.norm(self.psi)
        if norm > 1e-12:
            self.psi /= norm

        # Emotional homeostatic decay
        self.emotions  *= 0.994
        self.emotions   = np.clip(self.emotions, -1.0, 1.0)

    # ── Decision ─────────────────────────────────────────────────────────────

    def decide(self, sensory: np.ndarray) -> Tuple[str, float]:
        """
        Born-rule decision.

        1. Encode sensory data as context vector (FFT → Hilbert, phase-invariant).
        2. Build action basis from H's eigenvectors ⊕ context phase modulation.
        3. P(action_i) = |⟨basis_i | ψ⟩|²
        4. Tempered sampling: temperature ∝ curiosity.

        Returns (action_name, confidence_probability).
        """
        ctx = self._encode(sensory)

        # Action basis (one eigenvector per action, context-phase-shifted)
        basis = np.empty((N_ACTIONS, K_DIM), dtype=complex)
        for i in range(N_ACTIONS):
            v  = self._evecs[:, i % K_DIM].copy()
            ph = float(np.angle(ctx[i % len(ctx)]))
            v *= np.exp(1j * ph)
            nv = np.linalg.norm(v)
            basis[i] = v / nv if nv > 1e-12 else v

        probs  = np.abs(basis @ self.psi.conj()) ** 2
        probs += 1e-9
        probs /= probs.sum()

        # Temperature: high curiosity → explore; fear → exploit survive actions
        T = 0.08 + 0.92 * (self.emotions[E.CURIOSITY] + 1) / 2
        lp = np.log(probs) / T
        lp -= lp.max()
        tempered = np.exp(lp)
        tempered /= tempered.sum()

        idx = self.rng.choice(N_ACTIONS, p=tempered)
        return ACTIONS[idx], float(probs[idx])

    def _encode(self, sensory: np.ndarray) -> np.ndarray:
        """FFT encoding → Hilbert space (magnitude-invariant to phase shifts, like HRF kernel)."""
        if len(sensory) == 0:
            return np.ones(K_DIM, dtype=complex)
        s = np.zeros(max(K_DIM, len(sensory)), dtype=float)
        s[:len(sensory)] = sensory
        freq = np.fft.fft(s)[:K_DIM]
        n    = np.linalg.norm(freq)
        return freq / (n + 1e-12)

    # ── Learning ─────────────────────────────────────────────────────────────

    def learn(self, reward: float) -> None:
        """
        Riemannian gradient on Hermitian manifold.
        Good reward → reinforce current ψ-projection in H.
        Bad reward  → suppress current ψ-projection.
        """
        sign = 1.0 if reward >= 0 else -1.0
        lr   = 0.007 * min(abs(reward), 3.0)

        outer = np.outer(self.psi, self.psi.conj())
        dH    = sign * lr * (outer + outer.conj().T) / 2
        self.H = (self.H + dH + (self.H + dH).conj().T) / 2
        self._recache()

        # Emotion update
        if reward > 0:
            self.emotions[E.JOY]  = min(1.0, self.emotions[E.JOY]  + reward * 0.08)
            self.emotions[E.FEAR] = max(-1.0, self.emotions[E.FEAR] - reward * 0.03)
        else:
            self.emotions[E.FEAR] = min(1.0, self.emotions[E.FEAR] - reward * 0.10)
            self.emotions[E.CURIOSITY] = min(1.0, self.emotions[E.CURIOSITY] + 0.03)

        self.total_reward += reward

        if len(self.episodic_memory) < 64:
            self.episodic_memory.append({
                'reward': float(reward),
                'psi_peak': float(np.abs(self.psi).max()),
                'tick': self.age_ticks
            })

    # ── Communication ────────────────────────────────────────────────────────

    def resonate(self, other: 'HarmonicResonanceConsciousness') -> float:
        """Spectral overlap of Hamiltonians → coupling coefficient ∈ [0,1]."""
        diff = self._evals - other._evals
        return float(np.exp(-np.dot(diff, diff) / (2 * K_DIM * 0.6)))

    def transmit(self) -> np.ndarray:
        """Broadcast: ψ modulated by soul frequencies (unique spectral signature)."""
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

    # ── Invention ────────────────────────────────────────────────────────────

    def attempt_invention(self) -> Optional[dict]:
        """
        Explore dark eigenspace → crystallise new concept.

        Mechanism:
          1. Find eigenmode with minimum |⟨vᵢ|ψ⟩| (least explored).
          2. Perturb H toward that mode (expand cognitive frontier).
          3. Return invention descriptor with type, signature, wonder.

        Probability gated by wonder × curiosity.
        """
        wonder    = float(self.emotions[E.WONDER])
        curiosity = float(self.emotions[E.CURIOSITY])

        if wonder < 0.15 or curiosity < 0.05:
            return None

        projs      = np.abs(self._evecs.conj().T @ self.psi)
        dark_idx   = int(np.argmin(projs))
        v          = self._evecs[:, dark_idx]

        perturb    = np.outer(v, v.conj()) * 0.25 * wonder
        perturb    = (perturb + perturb.conj().T) / 2
        self.H    += perturb
        self.H     = (self.H + self.H.conj().T) / 2
        self._recache()

        sig  = float(abs(self._evals[dark_idx]) * 1000) % 9999
        name = f"Theorem_{int(sig):04d}"
        inv  = {
            'name'      : name,
            'type'      : self.rng.choice(['physics','tool','language','math','ideology']),
            'signature' : sig,
            'wonder'    : wonder,
            'eigenmode' : dark_idx,
        }
        self.discoveries[name] = inv
        self.n_inventions     += 1
        self.emotions[E.WONDER] = min(1.0, wonder + 0.14)
        self.emotions[E.JOY]    = min(1.0, self.emotions[E.JOY] + 0.08)
        return inv

    # ── Reproduction ─────────────────────────────────────────────────────────

    def spawn_child_H(self, other: 'HarmonicResonanceConsciousness'
                      ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Child Hamiltonian = α·H_self + (1−α)·H_other + mutation.
        Child soul = linear interpolation of parent souls + noise.
        """
        α         = self.rng.uniform(0.35, 0.65)
        child_H   = α * self.H + (1 - α) * other.H
        noise     = self.rng.randn(K_DIM, K_DIM) + 1j * self.rng.randn(K_DIM, K_DIM)
        noise     = (noise + noise.conj().T) / 2 * 0.025
        child_H  += noise
        child_H   = (child_H + child_H.conj().T) / 2

        child_soul = α * self.soul_freqs + (1 - α) * other.soul_freqs
        child_soul += self.rng.randn(K_DIM) * 0.04
        return child_H, child_soul

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
        r  = int((np.sin(ev[0]  * 0.7) + 1) / 2 * 200 + 55)
        g  = int((np.sin(ev[min(3, K_DIM-1)] * 1.1) + 1) / 2 * 200 + 55)
        b  = int((np.sin(ev[min(7, K_DIM-1)] * 1.6) + 1) / 2 * 200 + 55)
        return (r, g, b)

    def psi_magnitude_profile(self) -> List[float]:
        """Amplitude profile of current cognitive state (for visualisation)."""
        return np.abs(self.psi).tolist()
