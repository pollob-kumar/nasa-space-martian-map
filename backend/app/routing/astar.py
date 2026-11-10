"""8-connected A* over a cost grid. cost=inf means blocked."""
import heapq
import math
import numpy as np

_NEIGHBOURS = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
               (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))]


def astar(cost: np.ndarray, start: tuple[int, int], goal: tuple[int, int]):
    """cost[r,c] = multiplier >=1 (per metre-ish), inf = blocked. Returns list of (row,col) or None."""
    h, w = cost.shape
    if not (np.isfinite(cost[start]) and np.isfinite(cost[goal])):
        return None

    def heur(r, c):
        return math.hypot(goal[0] - r, goal[1] - c)  # admissible: min multiplier is 1

    open_heap = [(heur(*start), 0.0, start)]
    g_score = {start: 0.0}
    came = {}
    closed = set()
    while open_heap:
        _, g, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        if cur == goal:
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            return path[::-1]
        closed.add(cur)
        r, c = cur
        for dr, dc, step in _NEIGHBOURS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            m = cost[nr, nc]
            if not np.isfinite(m):
                continue
            # no corner cutting through blocked cells
            if dr and dc and (not np.isfinite(cost[r + dr, c]) or not np.isfinite(cost[r, c + dc])):
                continue
            ng = g + step * 0.5 * (cost[r, c] + m)
            if ng < g_score.get((nr, nc), float("inf")):
                g_score[(nr, nc)] = ng
                came[(nr, nc)] = cur
                heapq.heappush(open_heap, (ng + heur(nr, nc), ng, (nr, nc)))
    return None
