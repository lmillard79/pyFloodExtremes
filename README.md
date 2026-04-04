# pyFloodExtremes

**Bayesian and frequentist flood frequency analysis for Australian catchments.**

`pyFloodExtremes` fits extreme value distributions to annual maximum streamflow records, produces flood frequency curves with uncertainty bands, and compares results across multiple modelling approaches — all following Australian Rainfall and Runoff (ARR 2019) conventions.

It is designed as both a **practical analysis tool** and a **learning resource** for engineers and hydrologists working with Australian flood data.

---
# ⚠️ Educational Demo Package

**This package is for learning purposes only.** 
It is not intended for production or professional practice use. It may contain bugs, other issues, 
and breaking changes without notice.

## What does it do?

Given a record of annual maximum flows from a gauge station, `pyFloodExtremes` will:

- Estimate the **magnitude of floods at any return period** (e.g., the 1% AEP / 100-year flood)
- Quantify the **uncertainty** in those estimates honestly, using either Bayesian credible intervals or bootstrap confidence limits
- Detect and handle **low-flow outliers** (PILFs) using the Multiple Grubbs-Beck Test recommended by ARR 2019
- Compare three different modelling approaches side-by-side so you can see how distribution choice affects design flood estimates

### The scientific question this package explores

> *How does the choice of frequency distribution affect design flood estimates when the record contains a potentially extraordinary event?*

The example dataset contains 55 years of annual maximum flows (1970–2024) with a known outlier: the 2021 flood at **121.9 m³/s — nearly double the next highest event** (48.3 m³/s in 2022). This single event drives meaningful differences between models and makes the dataset an ideal case study for understanding the limits and strengths of each approach.

---

## Expected results

The table below shows posterior median design flood estimates at standard Australian design AEPs, produced by running all three models on the included example dataset. This is what you should see after completing the setup below.

| AEP (%) | ARI (years) | GEV (m³/s) | LP3 (m³/s) | TCEV (m³/s) |
|---|---|---|---|---|
| 10% | 10 | 27.7 | 29.2 | 27.7 |
| 5% | 20 | 36.5 | 39.1 | 36.6 |
| 2% | 50 | 51.3 | 55.3 | 52.7 |
| 1% | 100 | 65.4 | 70.2 | 68.2 |
| 0.5% | 200 | 83.0 | 88.2 | 86.9 |
| 0.2% | 500 | 112.1 | 117.3 | 116.5 |
| 0.05% | 2000 | 175.2 | 176.1 | 173.6 |

All three models agree closely at frequent return periods. The differences at rare events, and the width of the uncertainty bands, tell the more important story — explored in detail in the notebooks.

---

## Notebooks

Each notebook is self-contained and runs top-to-bottom. Click the **View** link to see a fully executed version with all plots and outputs before downloading anything.

| # | Topic | What you will learn | View |
|---|---|---|---|
| 01 | GEV — Generalised Extreme Value | Extreme value theory, Bayesian inference, NUTS sampling, what divergences mean, how to read trace and corner plots | [![nbviewer](https://img.shields.io/badge/view-nbviewer-orange?logo=jupyter)](https://nbviewer.org/github/lmillard79/pyFloodExtremes/blob/main/notebooks/01_gev_demo.ipynb) |
| 02 | LP3 — Log-Pearson Type 3 | Why LP3 is the ARR standard, log-space fitting, skewness parameter instability | [![nbviewer](https://img.shields.io/badge/view-nbviewer-orange?logo=jupyter)](https://nbviewer.org/github/lmillard79/pyFloodExtremes/blob/main/notebooks/02_lp3_demo.ipynb) |
| 03 | TCEV — Two-Component Mixture | Physically distinct flood populations, label switching, component separation | [![nbviewer](https://img.shields.io/badge/view-nbviewer-orange?logo=jupyter)](https://nbviewer.org/github/lmillard79/pyFloodExtremes/blob/main/notebooks/03_tcev_demo.ipynb) |
| 04 | Model Comparison | GEV vs LP3 vs TCEV side-by-side, design flood table, what uncertainty dominates | [![nbviewer](https://img.shields.io/badge/view-nbviewer-orange?logo=jupyter)](https://nbviewer.org/github/lmillard79/pyFloodExtremes/blob/main/notebooks/04_comparison.ipynb) |
| 05 | MGBT — Low Outlier Detection | What PILFs are, the Grubbs-Beck test, left-censoring vs deletion | [![nbviewer](https://img.shields.io/badge/view-nbviewer-orange?logo=jupyter)](https://nbviewer.org/github/lmillard79/pyFloodExtremes/blob/main/notebooks/05_mgbt_demo.ipynb) |
| 06 | FLIKE Emulator — LH-moments | L-moments vs Bayesian, the shift parameter, bootstrap uncertainty, FLIKE comparison | [![nbviewer](https://img.shields.io/badge/view-nbviewer-orange?logo=jupyter)](https://nbviewer.org/github/lmillard79/pyFloodExtremes/blob/main/notebooks/06_flike_emulator.ipynb) |

> **If your results look different to the nbviewer outputs**, the setup instructions below will help you confirm your environment is correct. Small numerical differences between runs are normal (MCMC sampling is random); large differences suggest an environment issue.

---

## Setup

### What you need first

Before starting, you need three things installed on your computer:

1. **Python 3.10 or later** — check by opening a terminal and running `python --version`. If you need to install it, download from [python.org](https://www.python.org/downloads/).

2. **uv** — a fast Python package manager that handles all dependencies automatically. Install it with one command:
   - **Windows** (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - **Mac / Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Or see the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for alternatives.

3. **Git** — to download the repository. Check with `git --version`. If not installed, download from [git-scm.com](https://git-scm.com/).

You do **not** need to install Jupyter, PyMC, ArviZ, or any other library separately — `uv` handles all of that in the next step.

---

### Installation — step by step

**Step 1: Download the repository**

Open a terminal (Command Prompt, PowerShell, or Terminal on Mac/Linux) and run:

```bash
git clone https://github.com/lmillard79/pyFloodExtremes.git
cd pyFloodExtremes
```

This creates a folder called `pyFloodExtremes` on your computer and moves you into it.

> **No git?** You can also click the green **Code** button on the GitHub page and select **Download ZIP**, then unzip it and open a terminal inside the folder.

---

**Step 2: Install all dependencies**

```bash
uv sync
```

This will download and install Python, PyMC, ArviZ, Jupyter, and all other required libraries into an isolated environment inside the project folder. It should take 1–3 minutes the first time. You will see output like:

```
Resolved 146 packages in ...
Installed 146 packages in ...
```

You only need to do this once. The environment is stored in `.venv/` inside the project folder and does not affect anything else on your computer.

---

**Step 3: Open the notebooks**

```bash
uv run jupyter notebook
```

This opens Jupyter in your browser. Navigate to the `notebooks/` folder and open any notebook. Start with `01_gev_demo.ipynb`.

> **Tip — Windows users:** If Jupyter opens but the kernel shows as "dead" or the notebook fails to run, the kernel may need to be pointed at the correct Python environment. Go to **Kernel → Change Kernel** and select `pyfloodextremes`. If it is not listed, run this command in your terminal and then restart Jupyter:
> ```bash
> uv run python -m ipykernel install --user --name pyfloodextremes --display-name "pyfloodextremes"
> ```

---

### Running a notebook for the first time

Once a notebook is open:

1. Go to **Kernel → Restart & Clear Output** to start fresh.
2. Run all cells in order: **Cell → Run All** (or press `Shift+Enter` to run one cell at a time).
3. The first fitting cell will take **30–60 seconds** as PyMC runs MCMC sampling. A progress bar will appear. This is normal.
4. Notebook 04 (comparison) fits three models sequentially and takes **2–4 minutes** total.

You will see sampling messages like:
```
Sampling 4 chains for 1_000 tune and 2_000 draw iterations...
```
and possibly warnings about **divergences**. These are explained inside each notebook — in most cases they do not affect the validity of the results.

---

## Using your own data

The example dataset is in `data/AMS.csv`. To use your own gauge record:

1. Prepare a CSV with columns `year`, `water_level_mAHD`, and `flow_m3s`.
2. Replace the file path in the notebook's data loading cell:
   ```python
   df = load_ams("../data/your_data.csv")
   ```
3. Run the notebook as normal.

The models work best with at least 20 years of data. Records shorter than 15 years will produce very wide uncertainty bands — this is expected and correct, not a bug.

---

## Background: distributions and methods

| Method | Distribution | Approach | Primary use |
|---|---|---|---|
| `fit_gev` | Generalised Extreme Value (GEV) | Bayesian MCMC | Theoretically motivated for annual maxima |
| `fit_lp3` | Log-Pearson Type 3 (LP3) | Bayesian MCMC | ARR 2019 default for Australian practice |
| `fit_tcev` | Two-Component Extreme Value (TCEV) | Bayesian MCMC | Records with physically distinct flood populations |
| `FLIKE(model_type="gev/lp3")` | GEV or LP3 | LH-moments + bootstrap | Frequentist; directly comparable to TUFLOW FLIKE |
| `detect_low_outliers` | — | Multiple Grubbs-Beck Test | ARR 2019 preprocessing for low outlier detection |

All Bayesian fits use PyMC's NUTS sampler and return ArviZ `InferenceData` objects. Uncertainty is expressed as **94% Highest Density Intervals (HDI)** throughout — the narrowest interval containing 94% of the posterior probability mass.

Plots follow ARR 2019 conventions: Annual Exceedance Probability (AEP) on the x-axis on a probability scale, flow (m³/s) on a log y-axis, with Cunnane plotting positions for observed data.

For theoretical background on the distributions and methods, see the [`docs/theory/`](docs/theory/) folder.

---

## Package structure

```
pyFloodExtremes/
├── src/flood_ffa/
│   ├── gev/          # GEV fitting (Bayesian + LH-moments)
│   ├── lp3/          # LP3 fitting (Bayesian + LH-moments)
│   ├── tcev/         # TCEV mixture model fitting
│   ├── preprocessing/# MGBT low outlier detection
│   ├── stats/        # LH-moments engine and bootstrap
│   ├── data/         # Data loader (load_ams, get_flow_series)
│   ├── compare.py    # Multi-model comparison plot
│   ├── flike.py      # FLIKE emulator orchestrator
│   └── plots_lh.py   # LH-moments probability plots
├── notebooks/        # Six demonstration notebooks
├── data/
│   └── AMS.csv       # 55-year example dataset (1970–2024)
├── docs/
│   └── theory/       # Technical background on EVT, LP3, FLIKE, Bayesian inference
└── tests/
```

---

## Requirements

- Python 3.10+
- PyMC 5+
- ArviZ
- NumPy, SciPy, pandas, matplotlib
- probscale
- Jupyter

All managed automatically by `uv sync`.

---

## Acknowledgements

Built on [PyMC](https://www.pymc.io) and [ArviZ](https://python.arviz.org). LH-moments implementation follows Wang (1997) and Kuczera (1999). MGBT ported from the reference implementation at [MGBT_1.0.7](https://github.com/wasquith-usgs/mgbt). Australian plotting conventions follow ARR 2019.

---

## Licence

MIT — see `LICENSE`.
