# ⚡ Quantitative Triangular Arbitrage Scanner (Bellman-Ford Engine)

> Sub-millisecond negative-cycle detection engine across high-frequency crypto orderbooks, factoring in bidirectional taker fees and slippage hurdles.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📌 Architecture & Mathematical Formulation

Triangular arbitrage occurs when exchange rate discrepancies between three or more currencies allow a trader to start with Currency $A$, trade sequentially through $B$ and $C$, and return to $A$ with a net positive yield.

### 1. Negative-Cycle Equivalence
Rather than searching for cyclic products where $\prod \text{rate}_i > 1$, we map currency conversion rates into a directed graph $G = (V, E)$ with edge weights:

$$w(u, v) = -\ln\Big(\text{Rate}(u, v) \cdot (1 - \text{Fee})\Big)$$

By applying the logarithmic transformation:
- Finding a profitable trade cycle $\prod (r_i \cdot (1 - f)) > 1$ is mathematically identical to finding a **negative-weight directed cycle**:
$$\sum -\ln\Big(r_i \cdot (1 - f)\Big) < 0$$
- This allows execution of the classical **Bellman-Ford algorithm** in $\mathcal{O}(|V| \cdot |E|)$ time, reliably identifying optimal risk-free arbitrage opportunities in under **0.2 milliseconds**.

---

## 🚀 Key Features

- **Blazingly Fast Graph Engine**: Solves $|V| = 5, |E| = 16$ cross-currency books in $<0.15\text{ms}$.
- **Realistic Fee Modeling**: Incorporates exchange maker/taker fee tiers (e.g. 0.075% VIP0) per execution leg.
- **Multi-Exchange Cross-Rate Simulator**: High-frequency synthetic tick stream simulating transient mispricings between Binance, Coinbase, and Kraken.
- **REST API + WebSocket**: Built on FastAPI with `/api/v1/scan` and `/api/v1/custom-scan` endpoints.
- **Glassmorphic Quant Dashboard**: Real-time visualization of cross-rate matrix, active arbitrage execution cycles, and audio alerts.

---

## 🛠️ Project Structure

```
crypto-arbitrage-scanner/
├── api/
│   └── main.py              # FastAPI REST service & static web mount
├── src/
│   ├── graph_arbitrage.py   # ArbitrageGraph with Bellman-Ford negative-cycle solver
│   └── orderbook_stream.py  # Orderbook tick generator with transient spread anomalies
├── web/
│   ├── index.html           # Dark-mode Quant trading dashboard
│   ├── style.css            # Responsive glassmorphism styling
│   └── app.js               # Polling client with WebAudio arbitrage alerts
├── tests/
│   └── test_arbitrage.py    # Pytest test suite (cycle verification & fee hurdles)
├── cli.py                   # High-performance ANSI terminal scanner
├── requirements.txt
└── README.md
```

---

## ⚡ Quickstart

### 1. Installation
```bash
git clone https://github.com/JayNabasu/crypto-arbitrage-scanner.git
cd crypto-arbitrage-scanner
pip install -r requirements.txt
```

### 2. Run CLI Scanner
```bash
python cli.py
```
*Sample Output:*
```
[Tick 01] Scanned 5 currencies, 16 pairs in 0.12ms
  [PROFITABLE CYCLE] ETH -> BTC -> USDT -> ETH
     Net Yield: +0.285% (Compounding Multiplier: 1.00285)
     Leg Rates: [0.053912, 64228.59, 0.00029]
```

### 3. Run FastAPI Quant Web Dashboard
```bash
python api/main.py
# Open browser at http://127.0.0.1:8005
```

### 4. Run Tests
```bash
python -m pytest tests/test_arbitrage.py -v
```

---

## 👤 Author
**Jerry A. Nabasu**  
- GitHub: [@JayNabasu](https://github.com/JayNabasu)  
- Email: [jerrynabasu@gmail.com](mailto:jerrynabasu@gmail.com)
