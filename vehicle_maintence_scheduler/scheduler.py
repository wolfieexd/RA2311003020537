from logging_middleware.logger import Log

def knapsack(vehicles: list, capacity: int) -> dict:
    """
    0/1 Knapsack via Dynamic Programming
    Time: O(n * capacity) | Space: O(n * capacity)
    """
    Log("backend", "info", "service", f"Starting knapsack: {len(vehicles)} vehicles, capacity={capacity}")
    n = len(vehicles)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        duration = vehicles[i-1]["Duration"]
        impact = vehicles[i-1]["Impact"]
        for w in range(capacity + 1):
            dp[i][w] = dp[i-1][w]
            if duration <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w - duration] + impact)

    # Backtrack to find selected vehicles
    selected, w = [], capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(vehicles[i-1])
            w -= vehicles[i-1]["Duration"]

    result = {
        "selected_vehicles": selected,
        "total_impact": dp[n][capacity],
        "hours_used": sum(v["Duration"] for v in selected)
    }
    Log("backend", "info", "service", f"Knapsack complete: impact={result['total_impact']}, hours_used={result['hours_used']}")
    return result
