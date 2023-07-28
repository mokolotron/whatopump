import heapq

class CurrencyGraph:
    def __init__(self):
        self.graph = {}

    def add_edge(self, base, quote, rate):
        if base not in self.graph:
            self.graph[base] = {}
        self.graph[base][quote] = rate

        if quote not in self.graph:
            self.graph[quote] = {}
        self.graph[quote][base] = 1.0 / rate

    def convert_currency(self, start_currency, target_currency, amount):
        if start_currency not in self.graph or target_currency not in self.graph:
            raise ValueError("Invalid currency")

        # Dijkstra's algorithm
        min_heap = [(1.0, start_currency)]
        visited = set()

        while min_heap:
            current_rate, current_currency = heapq.heappop(min_heap)

            if current_currency in visited:
                continue

            visited.add(current_currency)

            if current_currency == target_currency:
                return amount * current_rate

            for neighbor, rate in self.graph[current_currency].items():
                if neighbor not in visited:
                    heapq.heappush(min_heap, (current_rate * rate, neighbor))

        raise ValueError("No conversion path exists")

# # Example usage:
# graph = CurrencyGraph()
# graph.add_edge("USD", "EUR", 0.85)
# graph.add_edge("EUR", "CONT", 0.5)
# # graph.add_edge("EUR", "GBP", 0.89)
# graph.add_edge("USD", "GBP", 0.75)
#
# start_currency = "GBP"
# target_currency = "CONT"
# amount = 1000
#
# try:
#     result = graph.convert_currency(start_currency, target_currency, amount)
#     print(f"{amount} {start_currency} is equal to {result:.2f} {target_currency}")
# except ValueError as e:
#     print(e)