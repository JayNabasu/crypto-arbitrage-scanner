"""
Unit tests for Graph-Based Triangular Arbitrage Engine and Bellman-Ford Cycle Detection.
"""

import pytest
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph_arbitrage import ArbitrageGraph, ArbitrageOpportunity
from src.orderbook_stream import generate_live_market_graph

def test_no_arbitrage_in_equilibrium():
    """When all cross-rates are strictly consistent, no arbitrage should be found."""
    graph = ArbitrageGraph(fee_pct=0.001) # 0.1% fee
    # EUR/USD = 1.10, GBP/USD = 1.30 -> EUR/GBP = 1.10 / 1.30 = 0.84615
    graph.update_rate("EUR", "USD", 1.10)
    graph.update_rate("USD", "EUR", 1.0 / 1.10)
    
    graph.update_rate("GBP", "USD", 1.30)
    graph.update_rate("USD", "GBP", 1.0 / 1.30)

    graph.update_rate("EUR", "GBP", 1.10 / 1.30)
    graph.update_rate("GBP", "EUR", 1.30 / 1.10)

    opps = graph.find_arbitrage_cycles()
    assert len(opps) == 0, "Equilibrium graph should yield zero profitable arbitrage cycles."

def test_synthetic_arbitrage_cycle_detected():
    """Inject a clear synthetic arbitrage cycle exceeding fees."""
    # Triangular cycle: USD -> BTC -> ETH -> USD
    # Rates:
    # 1 USD = 0.00002 BTC (BTC = 50,000 USD)
    # 1 BTC = 20 ETH (ETH = 2,500 USD)
    # Mispriced ETH: 1 ETH = 2,800 USD (instead of 2,500)
    # Compounding: 1 * 0.00002 * 20 * 2800 = 1.12 (12% gross profit)
    graph = ArbitrageGraph(fee_pct=0.00075) # 0.075% per trade
    graph.update_rate("USD", "BTC", 0.00002)
    graph.update_rate("BTC", "ETH", 20.0)
    graph.update_rate("ETH", "USD", 2800.0)

    opps = graph.find_arbitrage_cycles()
    assert len(opps) > 0, "Engine should detect synthetic mispricing."
    best = opps[0]
    assert best.profit_pct > 10.0
    assert best.effective_multiplier > 1.10

def test_market_stream_generation():
    """Ensure market stream generator produces valid graph with positive rates."""
    graph = generate_live_market_graph(inject_anomaly=True)
    assert len(graph.currencies) >= 4
    for u in graph.rates:
        for v in graph.rates[u]:
            assert graph.rates[u][v] > 0.0

def test_arbitrage_opportunity_serialization():
    opp = ArbitrageOpportunity(["USDT", "BTC", "ETH", "USDT"], 0.45, 1.0045, [0.000015, 15.5, 3400.0])
    d = opp.to_dict()
    assert d["profit_pct"] == 0.45
    assert "USDT" in d["path"]
    assert len(d["rates"]) == 3
