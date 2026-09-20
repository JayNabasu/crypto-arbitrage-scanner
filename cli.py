"""
Live Terminal Dashboard for Crypto Triangular Arbitrage Scanner.
"""

import time
import sys
from pathlib import Path

# Ensure local imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.orderbook_stream import generate_live_market_graph

def run_cli_scanner(ticks: int = 10, delay_sec: float = 0.8):
    print("=" * 75)
    print(">> QUANTITATIVE TRIANGULAR ARBITRAGE SCANNER (BELLMAN-FORD ENGINE)")
    print("   Author: Jerry A. Nabasu (@JayNabasu)")
    print("   Fee Model: 0.075% Maker/Taker per leg | Min Profit Filter: 0.05%")
    print("=" * 75 + "\n")

    for i in range(1, ticks + 1):
        graph = generate_live_market_graph(inject_anomaly=(i % 2 == 1))
        start_time = time.perf_counter()
        opportunities = graph.find_arbitrage_cycles()
        scan_time_ms = (time.perf_counter() - start_time) * 1000

        print(f"[Tick {i:02d}] Scanned {len(graph.currencies)} currencies, {sum(len(v) for v in graph.rates.values())} pairs in {scan_time_ms:.2f}ms")

        if opportunities:
            for opp in opportunities[:2]:
                d = opp.to_dict()
                print(f"  [PROFITABLE CYCLE] {d['path']}")
                print(f"     Net Yield: +{d['profit_pct']:.3f}% (Compounding Multiplier: {d['effective_multiplier']})")
                print(f"     Leg Rates: {d['rates']}")
        else:
            print("  [INFO] Efficient Market: No negative cycles detected above fee threshold.")

        print("-" * 75)
        time.sleep(delay_sec)

if __name__ == "__main__":
    run_cli_scanner(ticks=5, delay_sec=0.2)

