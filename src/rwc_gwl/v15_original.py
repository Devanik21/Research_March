
# ==============================================================================
#  HARMONIC RESONANCE FIELDS (HRF) – v15.0 ULTIMATE (GPU EDITION)
# ==============================================================================
#  INSTALLATION & IMPORTS
# ==============================================================================
import subprocess
import sys

def install_rapids():
    print("Installing NVIDIA RAPIDS (cuML & cuDF) for GPU Acceleration...")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "cudf-cu12", "cuml-cu12",
                           "--extra-index-url=https://pypi.nvidia.com"])
    print("Installation Complete. Importing libraries...")

try:
    import cuml
    import cupy as cp
except ImportError:
    install_rapids()
    import cuml
    import cupy as cp

from sklearn.base import BaseEstimator, ClassifierMixin
import numpy as np
from cuml.neighbors import NearestNeighbors as cuNN
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.metrics import accuracy_score
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn.ensemble import BaggingClassifier

# ==============================================================================
#  HRF CORE CLASSIFIER (GPU OPTIMIZED)
# ==============================================================================

class HarmonicResonanceClassifier_v15(BaseEstimator, ClassifierMixin):
    # Global list to track every single accuracy found across all trees
    all_evolution_scores = []

    def __init__(self, auto_evolve=True):
        self.auto_evolve = auto_evolve
        self.base_freq = 10.0
        self.gamma = 0.5
        self.n_neighbors = 5
        self.scaler_ = RobustScaler(quantile_range=(15.0, 85.0))

    def _apply_bipolar_montage(self, X):
        X = np.clip(X, -15, 15)
        diffs = []
        for i in range(X.shape[1] - 1):
            diffs.append(X[:, i] - X[:, i + 1])
        coherence = np.var(X, axis=1).reshape(-1, 1)
        return np.hstack([X, np.array(diffs).T, coherence])

    def fit(self, X, y):
        X, y = check_X_y(X, y)
        y = y.astype(int)

        self.classes_ = np.unique(y)
        self.classes_gpu_ = cp.asarray(self.classes_)

        X_scaled = self.scaler_.fit_transform(X)
        self.X_train_ = self._apply_bipolar_montage(X_scaled)
        self.y_train_ = y

        if self.auto_evolve:
            n_sub = len(X)
            X_sub = self.X_train_[:n_sub]
            y_sub = y[:n_sub]

            X_tr, X_val, y_tr, y_val = train_test_split(
                X_sub, y_sub, test_size=0.24, stratify=y_sub, random_state=9
            )

            best_score = -1
            best_dna = (self.base_freq, self.gamma, self.n_neighbors)

            golden_grid = [
                (28.0, 10.0, 2), (30.0, 10.0, 1), (30.0, 10.0, 2), (50.0, 15.0, 2),
                (22.0, 9.0, 2), (18.0, 7.5, 2), (14.0, 5.0, 3), (16.0, 5.5, 3),
                (29.0, 10.0, 2), (31.0, 10.5, 2), (32.0, 11.0, 2), (33.0, 11.5, 2),
                (27.0, 9.5, 2), (26.0, 9.0, 2), (35.0, 12.0, 2), (34.0, 11.8, 2),
                (50.0, 15.0, 1), (52.0, 16.0, 2), (55.0, 17.0, 2), (60.0, 20.0, 2),
                (45.0, 13.5, 2), (48.0, 14.5, 2), (58.0, 19.0, 2), (65.0, 22.0, 2),
                (80.0, 25.0, 1), (90.0, 30.0, 1), (100.0, 35.0, 1), (120.0, 40.0, 1),
                (75.0, 24.0, 1), (85.0, 28.0, 1), (95.0, 32.0, 1), (110.0, 38.0, 1)
            ]

            for freq, gamma, k in golden_grid:
                preds = self._simulate_predict(X_tr, y_tr, X_val, freq, gamma, k)
                score = accuracy_score(y_val, preds)

                # Automatically track all scores found
                HarmonicResonanceClassifier_v15.all_evolution_scores.append(score)

                if score > best_score:
                    best_score = score
                    best_dna = (freq, gamma, k)

            self.base_freq, self.gamma, self.n_neighbors = best_dna
        return self

    def _simulate_predict(self, X_train, y_train, X_query, freq, gamma, k):
        X_tr_g, y_tr_g, X_q_g = cp.asarray(X_train), cp.asarray(y_train), cp.asarray(X_query)
        knn = cuNN(n_neighbors=k)
        knn.fit(X_tr_g)
        dists, indices = knn.kneighbors(X_q_g)

        w = cp.exp(-gamma * dists**2.5) * (1.0 + cp.cos(freq * dists))
        local_y = y_tr_g[indices]
        energies = cp.zeros((X_q_g.shape[0], len(self.classes_)))

        for ci, c in enumerate(self.classes_):
            mask = (local_y == c)
            energies[:, ci] = cp.sum(w * mask, axis=1)

        preds_gpu = cp.argmax(energies, axis=1)
        final_preds_gpu = self.classes_gpu_[preds_gpu]
        return cp.asnumpy(final_preds_gpu)

    def predict(self, X):
        check_is_fitted(self, ["X_train_", "y_train_"])
        X = check_array(X)
        X_scaled = self.scaler_.transform(X)
        X_holo = self._apply_bipolar_montage(X_scaled)
        return self._simulate_predict(self.X_train_, self.y_train_, X_holo, self.base_freq, self.gamma, self.n_neighbors)

# ==============================================================================
#  HRF ENSEMBLE (FOREST)
# ==============================================================================

def HarmonicResonanceForest_Ultimate(n_estimators=100):
    return BaggingClassifier(
        estimator=HarmonicResonanceClassifier_v15(auto_evolve=True),
        n_estimators=n_estimators,
        max_samples=0.75,
        bootstrap=True,
        n_jobs=1,
        random_state=21)