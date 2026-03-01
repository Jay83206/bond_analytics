# 📈 Bond Analytics Dashboard

An interactive Streamlit app for fixed-income analysis covering:
- **Bond Pricing** vs YTM
- **Macaulay & Modified Duration**
- **Convexity**
- **Yield Shock Scenarios** (±50, ±100, ±200 bps)

---

## 🚀 Deploy to Streamlit Community Cloud

### Step 1 — Push to GitHub
1. Create a new **public** GitHub repository (e.g. `bond-analytics-dashboard`).
2. Upload these files maintaining this structure:

```
bond-analytics-dashboard/
├── app.py
├── requirements.txt
└── .streamlit/
    └── config.toml
```

> **Tip:** The `.streamlit/` folder must be at the repo root (same level as `app.py`).

### Step 2 — Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **"New app"**.
3. Select your repository, branch (`main`), and set **Main file path** → `app.py`.
4. Click **"Deploy"** — the app will be live in ~2 minutes.

---

## 🖥️ Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## ⚙️ Features & Controls

| Sidebar Control | Description |
|---|---|
| Face Value | Par value of bond (default $1,000) |
| Maturity | Years to maturity (1–30) |
| Payment Frequency | Annual / Semi-Annual / Quarterly / Monthly |
| Coupon Range & Step | Min/max/step for coupon rates |
| YTM Range & Step | Min/max/step for yield scenarios |

## 📑 Dashboard Tabs

| Tab | Content |
|---|---|
| 📊 Dashboard | Full 5-row × N-col subplot matrix |
| 💹 Price Analysis | Price curves + heatmap |
| ⏱ Duration | Macaulay & Modified duration charts |
| 🔄 Convexity | Convexity curves + shock bar charts |
| 📋 Data Table | Sortable table + CSV download |

---

## 🔢 Bond Math

All calculations use pure Python (no external pricing library):

```
Bond Price    = Σ CF_t / (1 + y/f)^t
Macaulay Dur  = Σ [t × PV(CF_t)] / Price / f
Modified Dur  = Macaulay Dur / (1 + y/f)
Convexity     = Σ [PV(CF_t) × t × (t+1)] / [Price × (1+y/f)²] / f²
ΔP/P          ≈ –ModDur × Δy + 0.5 × Convexity × Δy²
```
