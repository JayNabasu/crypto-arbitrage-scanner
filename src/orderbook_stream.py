"""
Orderbook Telemetry & Multi-Exchange Cross-Rate Simulator.
Simulates high-frequency tick feeds across Binance, Coinbase, and Kraken with transient price spreads.
"""

import random
from typing import Dict
from src.graph_arbitrage import ArbitrageGraph

BASE_PRICES = {
    "BTC": 64200.0,
    "ETH": 3450.0,
    "SOL": 145.0,
    "BNB": 580.0
}

def generate_live_market_graph(inject_anomaly: bool = True) -> ArbitrageGraph:
    graph = ArbitrageGraph(fee_pct=0.00075) # 0.075% fee per trade
    
    # 1. Base USDT quote rates
    btc_usdt = BASE_PRICES["BTC"] * (1.0 + random.uniform(-0.002, 0.002))
    eth_usdt = BASE_PRICES["ETH"] * (1.0 + random.uniform(-0.002, 0.002))
    sol_usdt = BASE_PRICES["SOL"] * (1.0 + random.uniform(-0.003, 0.003))
    bnb_usdt = BASE_PRICES["BNB"] * (1.0 + random.uniform(-0.003, 0.003))

    # Add bidirectional rates (buy and sell with spread)
    half_spread = 0.0002 # 0.02% bid-ask spread
    _add_pair(graph, "BTC", "USDT", btc_usdt, half_spread)
    _add_pair(graph, "ETH", "USDT", eth_usdt, half_spread)
    _add_pair(graph, "SOL", "USDT", sol_usdt, half_spread)
    _add_pair(graph, "BNB", "USDT", bnb_usdt, half_spread)

    # 2. Cross rates
    # Theoretical ETH/BTC = ETH_USDT / BTC_USDT
    eth_btc = eth_usdt / btc_usdt
    sol_btc = sol_usdt / btc_usdt
    sol_eth = sol_usdt / eth_usdt
    bnb_btc = bnb_usdt / btc_usdt

    # Inject transient price mismatch (e.g. temporary lag on ETH/BTC pair)
    if inject_anomaly:
        anomaly_factor = 1.0 + random.uniform(0.0035, 0.0085) # 0.35% to 0.85% spread
        eth_btc *= anomaly_factor

    _add_pair(graph, "ETH", "BTC", eth_btc, half_spread)
    _add_pair(graph, "SOL", "BTC", sol_btc, half_spread)
    _add_pair(graph, "SOL", "ETH", sol_eth, half_spread)
    _add_pair(graph, "BNB", "BTC", bnb_btc, half_spread)

    return graph

def _add_pair(graph: ArbitrageGraph, base: str, quote: str, price: float, half_spread: float):
    # Selling base for quote: rate = price * (1 - half_spread)
    graph.update_rate(base, quote, price * (1.0 - half_spread))
    # Buying base with quote: rate = 1 / (price * (1 + half_spread))
    graph.update_rate(quote, base, 1.0 / (price * (1.0 + half_spread)))
