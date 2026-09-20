"""
FastAPI REST API & WebSocket Stream for Crypto Triangular Arbitrage Scanner.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph_arbitrage import ArbitrageGraph
from src.orderbook_stream import generate_live_market_graph

app = FastAPI(
    title="Quantitative Triangular Arbitrage Scanner API",
    description="Sub-millisecond Bellman-Ford Negative Cycle Detection across High-Frequency Orderbooks",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount web frontend
web_dir = Path(__file__).resolve().parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

@app.get("/")
def get_index():
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Triangular Arbitrage Scanner API is running. See /docs for Swagger UI."}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "crypto-arbitrage-scanner", "engine": "Bellman-Ford"}

@app.get("/api/v1/scan")
def scan_markets():
    """Generates snapshot tick and runs Bellman-Ford negative cycle arbitrage detection."""
    graph = generate_live_market_graph(inject_anomaly=True)
    t0 = time.perf_counter()
    opportunities = graph.find_arbitrage_cycles()
    latency_ms = (time.perf_counter() - t0) * 1000

    rates_matrix: Dict[str, Dict[str, float]] = {}
    for u in graph.rates:
        rates_matrix[u] = {v: round(graph.rates[u][v], 6) for v in graph.rates[u]}

    return {
        "timestamp": time.time(),
        "latency_ms": round(latency_ms, 3),
        "currencies_count": len(graph.currencies),
        "currencies": graph.currencies,
        "pairs_count": sum(len(v) for v in graph.rates.values()),
        "fee_pct": graph.fee_pct,
        "rates": rates_matrix,
        "opportunities": [opp.to_dict() for opp in opportunities]
    }

class CustomGraphRequest(BaseModel):
    fee_pct: float = 0.00075
    rates: List[Dict[str, Any]] # e.g. [{"from": "USDT", "to": "BTC", "rate": 0.0000155}]

@app.post("/api/v1/custom-scan")
def custom_scan(req: CustomGraphRequest):
    """Scan arbitrary currency pairs supplied by caller."""
    graph = ArbitrageGraph(fee_pct=req.fee_pct)
    for pair in req.rates:
        graph.update_rate(pair["from"], pair["to"], float(pair["rate"]))

    t0 = time.perf_counter()
    opps = graph.find_arbitrage_cycles()
    latency_ms = (time.perf_counter() - t0) * 1000

    return {
        "latency_ms": round(latency_ms, 3),
        "opportunities": [o.to_dict() for o in opps]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8005)
