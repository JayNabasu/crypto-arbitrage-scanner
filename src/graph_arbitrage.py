"""
Graph-Based Triangular Arbitrage Detection using the Bellman-Ford Algorithm.
Converts exchange rates to negative log weights: w = -ln(rate * (1 - fee)).
A negative cycle indicates a risk-free profitable arbitrage opportunity.
"""

import math
from typing import Dict, List, Tuple, Optional

class ArbitrageOpportunity:
    def __init__(self, path: List[str], profit_pct: float, effective_multiplier: float, rates: List[float]):
        self.path = path # e.g. ["USDT", "BTC", "ETH", "USDT"]
        self.profit_pct = profit_pct # e.g. 0.84%
        self.effective_multiplier = effective_multiplier # e.g. 1.0084
        self.rates = rates # exchange rates utilized across each leg

    def to_dict(self) -> dict:
        return {
            "path": " -> ".join(self.path),
            "currencies": self.path,
            "profit_pct": round(self.profit_pct, 3),
            "effective_multiplier": round(self.effective_multiplier, 5),
            "rates": [round(r, 6) for r in self.rates]
        }

class ArbitrageGraph:
    def __init__(self, fee_pct: float = 0.00075):
        """
        fee_pct: Trading fee per leg (default: 0.075% standard VIP0 maker/taker fee)
        """
        self.fee_pct = fee_pct
        self.currencies: List[str] = []
        self.rates: Dict[str, Dict[str, float]] = {}

    def update_rate(self, from_curr: str, to_curr: str, rate: float):
        if from_curr not in self.currencies:
            self.currencies.append(from_curr)
        if to_curr not in self.currencies:
            self.currencies.append(to_curr)

        if from_curr not in self.rates:
            self.rates[from_curr] = {}
        self.rates[from_curr][to_curr] = rate

    def find_arbitrage_cycles(self) -> List[ArbitrageOpportunity]:
        """Runs Bellman-Ford algorithm to identify negative cycles."""
        opportunities = []
        num_vertices = len(self.currencies)
        if num_vertices < 3:
            return opportunities

        # Build list of directed edges with negative log weights
        # weight = -ln(rate * (1 - fee))
        edges: List[Tuple[str, str, float, float]] = []
        for u in self.rates:
            for v in self.rates[u]:
                raw_rate = self.rates[u][v]
                effective_rate = raw_rate * (1.0 - self.fee_pct)
                if effective_rate > 0:
                    weight = -math.log(effective_rate)
                    edges.append((u, v, weight, raw_rate))

        # Check negative cycles starting from each currency base (especially USDT, USD, BTC)
        for source in self.currencies:
            opp = self._bellman_ford_cycle(source, edges)
            if opp and not any(o.path == opp.path for o in opportunities):
                opportunities.append(opp)

        # Sort by profit descending
        opportunities.sort(key=lambda o: o.profit_pct, reverse=True)
        return opportunities

    def _bellman_ford_cycle(self, source: str, edges: List[Tuple[str, str, float, float]]) -> Optional[ArbitrageOpportunity]:
        dist = {c: float("inf") for c in self.currencies}
        predecessor = {c: None for c in self.currencies}
        edge_rates = {}
        dist[source] = 0.0

        num_vertices = len(self.currencies)

        # Relax edges |V| - 1 times
        for _ in range(num_vertices - 1):
            for u, v, w, raw_rate in edges:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    predecessor[v] = u
                    edge_rates[(u, v)] = raw_rate

        # Check for negative-weight cycles on the |V|-th iteration
        for u, v, w, raw_rate in edges:
            if dist[u] + w < dist[v] - 1e-9:
                # Negative cycle detected! Trace back cycle path
                visited = {}
                curr = v
                for _ in range(num_vertices):
                    curr = predecessor[curr] or curr

                cycle = []
                trace = curr
                while True:
                    cycle.append(trace)
                    if trace == curr and len(cycle) > 1:
                        break
                    trace = predecessor[trace]
                    if not trace or len(cycle) > num_vertices + 1:
                        break

                cycle.reverse()
                if len(cycle) >= 4 and cycle[0] == cycle[-1]: # e.g. [USDT, BTC, ETH, USDT]
                    # Calculate true compounding multiplier
                    multiplier = 1.0
                    rates_used = []
                    for i in range(len(cycle) - 1):
                        from_c, to_c = cycle[i], cycle[i + 1]
                        rate = self.rates.get(from_c, {}).get(to_c, 1.0)
                        rates_used.append(rate)
                        multiplier *= rate * (1.0 - self.fee_pct)

                    profit_pct = (multiplier - 1.0) * 100.0
                    if profit_pct > 0.05: # Minimum threshold 0.05% net profit
                        return ArbitrageOpportunity(cycle, profit_pct, multiplier, rates_used)

        return None
