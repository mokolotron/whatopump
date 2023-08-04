import heapq

class CurrencyGraph:

    def __init__(self):
        self.graph = {}  # Initialize an empty dictionary to represent the currency graph.

    def add_edge(self, currency1, currency2, rate):
        """
        Add an edge between currency1 and currency2 with the given exchange rate (rate * fee).
        Also, add the reverse edge from currency2 to currency1 with the inverse rate (1.0 / rate * fee).
        """
        if currency1 not in self.graph:
            self.graph[currency1] = {}
        self.graph[currency1][currency2] = rate

    def convert_currency(self, start_currency, target_currency, amount):
        """
        Convert the given amount from start_currency to target_currency using Dijkstra's algorithm
        with storing predecessors to find the shortest conversion path.
        """

        if start_currency not in self.graph or target_currency not in self.graph:
            raise ValueError("Invalid currency")

        # Dijkstra's algorithm with storing predecessors
        min_heap = [(1.0, start_currency, None)]  # Priority queue to store currencies with their current rates.
        visited = set()  # Set to keep track of visited currencies.
        predecessors = {}  # Dictionary to store predecessors for constructing the conversion path.

        while min_heap:
            current_rate, current_currency, predecessor = heapq.heappop(min_heap)

            if current_currency in visited:
                continue

            visited.add(current_currency)
            predecessors[current_currency] = predecessor

            if current_currency == target_currency:
                # Reconstruct the shortest path
                path = [target_currency]
                while target_currency != start_currency:
                    target_currency = predecessors[target_currency]
                    path.append(target_currency)
                path.reverse()
                return amount * current_rate, path

            for neighbor, rate in self.graph[current_currency].items():
                if neighbor not in visited:
                    heapq.heappush(min_heap, (current_rate * rate, neighbor,
                                              current_currency))  # Add the neighbor to the min-heap with the updated rate

        raise ValueError("No conversion path exists")

# # Example usage: (deprecated)
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