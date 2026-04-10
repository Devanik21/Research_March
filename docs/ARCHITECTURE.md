# Architecture

## Project Structure

The repository houses two primary research projects under the `src/` directory:

1.  **`src/rwc_gwl/` (Riemannian Wave Classifier & Geometric Wave Learner)**
    *   Treats machine learning as a problem of wave physics on a Riemannian manifold.
    *   Classification is performed by measuring quantum-mechanical resonance energies on a continuously evolving geometric surface sculpted by discrete Ricci flow.
    *   Utilizes GPU acceleration via NVIDIA RAPIDS (cuML, cuDF) and CuPy.
    *   See RWC_GWL_WhitePaper.md and docs/Readme_1.md for in-depth mathematical foundations and iterative history.

2.  **`src/hyper/` (Event Horizon Spectral Life Simulator)**
    *   A simulation featuring agents, civilization dynamics, and a Streamlit frontend application (`app.py`).
    *   Components include `agents.py`, `civilization.py`, `consciousness.py`, `evolution.py`, `metacognition.py`, and `world.py`.
    *   See `src/hyper/HyperAgent_v4_Enhancement_Report.md` for detailed information on this project.

## Guiding Principles
*   **Organization:** The codebase maintains a highly organized, professional repository structure with dedicated subfolders for each distinct codebase.
*   **Immutability of Original Files:** We strictly adhere to not changing, cleaning, renaming, or deleting any original files (e.g., `app (1).py` or `rwc_gwl (1).py`).
