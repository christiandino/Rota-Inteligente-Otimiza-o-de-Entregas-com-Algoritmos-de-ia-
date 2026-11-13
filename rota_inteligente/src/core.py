"""Algoritmos de roteamento em grafo e agrupamento de entregas (sem dependências externas).

Conteúdo:
- load_data: lê nós, ruas (arestas) e pedidos a partir de CSVs.
- dijkstra, astar, bfs, dfs: buscas de caminho entre dois nós.
- kmeans: agrupamento não supervisionado das entregas por proximidade.
- cost_matrix / optimize_route / baseline: ordem de visitas de cada entregador.
"""
import csv
import heapq
import itertools
import math
from collections import deque
from pathlib import Path

MAX_STOPS = 8  # limite da busca exaustiva de permutações (8! = 40.320 ordens)


# ---------------------------------------------------------------------------
# Leitura dos dados
# ---------------------------------------------------------------------------
def load_data(folder):
    """Retorna (nodes, graph, deliveries).

    nodes: {id: (x, y)}
    graph: lista de adjacência {origem: {destino: minutos}}
    deliveries: lista de nós com pedido, na ordem do CSV
    """
    folder = Path(folder)
    with (folder / 'nodes.csv').open(encoding='utf-8', newline='') as f:
        nodes = {r['id']: (float(r['x']), float(r['y'])) for r in csv.DictReader(f)}

    graph = {n: {} for n in nodes}
    with (folder / 'edges.csv').open(encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            a, b, w = r['source'], r['target'], float(r['minutes'])
            if a not in graph or b not in graph or w <= 0:
                raise ValueError(f'Aresta inválida: {a}-{b} ({w})')
            graph[a][b] = w
            if r['bidirectional'].strip().lower() == 'true':
                graph[b][a] = w

    with (folder / 'deliveries.csv').open(encoding='utf-8', newline='') as f:
        deliveries = [r['node'] for r in csv.DictReader(f)]
    if any(n not in nodes for n in deliveries):
        raise ValueError('Entrega em nó desconhecido')
    return nodes, graph, deliveries


def _check(graph, *names):
    if any(n not in graph for n in names):
        raise ValueError('Nó desconhecido')


def reconstruct(prev, start, goal, cost):
    if math.isinf(cost):
        return [], math.inf
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return path[::-1], cost


def _path_cost(graph, path):
    return sum(graph[a][b] for a, b in zip(path, path[1:]))


# ---------------------------------------------------------------------------
# Buscas de caminho
# ---------------------------------------------------------------------------
def dijkstra(graph, start, goal, stats=None):
    """Menor caminho por peso (minutos). stats['expandidos'] conta nós expandidos."""
    _check(graph, start, goal)
    q = [(0, start)]
    dist = {start: 0}
    prev = {}
    expanded = 0
    while q:
        d, u = heapq.heappop(q)
        if d > dist[u]:
            continue
        expanded += 1
        if u == goal:
            break
        for v, w in graph[u].items():
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(q, (nd, v))
    if stats is not None:
        stats['expandidos'] = expanded
    return reconstruct(prev, start, goal, dist.get(goal, math.inf))


def heuristic_scale(graph, nodes):
    """Menor razão minutos/distância entre todas as arestas.

    h(n) = escala × distância_euclidiana(n, destino) nunca superestima o custo
    real (admissível) e respeita a desigualdade triangular (consistente).
    """
    ratios = [w / math.dist(nodes[u], nodes[v])
              for u, adj in graph.items() for v, w in adj.items()
              if math.dist(nodes[u], nodes[v]) > 0]
    return min(ratios) if ratios else 0.0


def astar(graph, nodes, start, goal, stats=None, scale=None):
    """A* com heurística euclidiana escalada. stats['expandidos'] conta nós expandidos."""
    _check(graph, start, goal)
    if scale is None:
        scale = heuristic_scale(graph, nodes)

    def h(n):
        return scale * math.dist(nodes[n], nodes[goal])

    q = [(h(start), 0, start)]
    g = {start: 0}
    prev = {}
    expanded = 0
    while q:
        _, cost, u = heapq.heappop(q)
        if cost > g[u] + 1e-10:
            continue
        expanded += 1
        if u == goal:
            if stats is not None:
                stats['expandidos'] = expanded
            return reconstruct(prev, start, goal, cost)
        for v, w in graph[u].items():
            nc = cost + w
            if nc < g.get(v, math.inf) - 1e-10:
                g[v] = nc
                prev[v] = u
                heapq.heappush(q, (nc + h(v), nc, v))
    if stats is not None:
        stats['expandidos'] = expanded
    return [], math.inf


def bfs(graph, start, goal):
    """Busca em largura: minimiza o NÚMERO de ruas, ignorando os pesos."""
    _check(graph, start, goal)
    q = deque([start])
    prev = {}
    seen = {start}
    while q:
        u = q.popleft()
        if u == goal:
            break
        for v in graph[u]:
            if v not in seen:
                seen.add(v)
                prev[v] = u
                q.append(v)
    if goal not in seen:
        return [], math.inf
    path, _ = reconstruct(prev, start, goal, 0)
    return path, _path_cost(graph, path)


def dfs(graph, start, goal):
    """Busca em profundidade: encontra UM caminho qualquer, sem garantia de ser o menor."""
    _check(graph, start, goal)
    stack = [start]
    prev = {}
    seen = {start}
    while stack:
        u = stack.pop()
        if u == goal:
            break
        for v in sorted(graph[u], reverse=True):  # ordem determinística
            if v not in seen:
                seen.add(v)
                prev[v] = u
                stack.append(v)
    if goal not in seen:
        return [], math.inf
    path, _ = reconstruct(prev, start, goal, 0)
    return path, _path_cost(graph, path)


# ---------------------------------------------------------------------------
# Agrupamento (aprendizado não supervisionado)
# ---------------------------------------------------------------------------
def kmeans(nodes, deliveries, k, iterations=100):
    """K-Means implementado do zero, com inicialização determinística (mais distantes)."""
    if not 1 <= k <= len(deliveries):
        raise ValueError('k inválido: use entre 1 e o número de entregas')
    points = [nodes[n] for n in deliveries]
    centers = [points[0]]
    while len(centers) < k:
        centers.append(max(points, key=lambda p: min(math.dist(p, c) for c in centers)))

    labels = [-1] * len(deliveries)
    for _ in range(iterations):
        new = [min(range(k), key=lambda j: (math.dist(p, centers[j]), j)) for p in points]
        groups = [[p for p, lab in zip(points, new) if lab == j] for j in range(k)]
        updated = [(sum(x for x, _ in grp) / len(grp), sum(y for _, y in grp) / len(grp))
                   if grp else centers[j] for j, grp in enumerate(groups)]
        if new == labels and updated == centers:
            break
        labels, centers = new, updated
    return [[n for n, lab in zip(deliveries, labels) if lab == j] for j in range(k)]


def inertia(nodes, groups):
    """Soma dos quadrados das distâncias ao centróide (métrica clássica do K-Means)."""
    total = 0.0
    for grp in groups:
        if not grp:
            continue
        pts = [nodes[n] for n in grp]
        cx = sum(x for x, _ in pts) / len(pts)
        cy = sum(y for _, y in pts) / len(pts)
        total += sum((x - cx) ** 2 + (y - cy) ** 2 for x, y in pts)
    return total


# ---------------------------------------------------------------------------
# Ordem das entregas
# ---------------------------------------------------------------------------
def cost_matrix(graph, nodes, points):
    """Calcula com A* (uma única vez) o menor tempo e caminho entre cada par de pontos."""
    scale = heuristic_scale(graph, nodes)
    matrix = {}
    for a in points:
        for b in points:
            matrix[a, b] = astar(graph, nodes, a, b, scale=scale)
    return matrix


def route_cost(graph, nodes, route, matrix=None):
    """Custo total de uma rota (sequência de paradas) e os trechos percorridos."""
    if matrix is None:
        matrix = cost_matrix(graph, nodes, set(route))
    total = 0
    segments = []
    for a, b in zip(route, route[1:]):
        path, cost = matrix[a, b]
        if math.isinf(cost):
            return math.inf, []
        total += cost
        segments.append(path)
    return total, segments


def optimize_route(graph, nodes, stops, depot='D', matrix=None):
    """Busca exaustiva: testa todas as ordens das paradas, saindo e voltando ao depósito."""
    if len(stops) > MAX_STOPS:
        raise ValueError(f'Máximo de {MAX_STOPS} entregas por grupo na busca exata')
    if not stops:
        return [depot, depot], 0
    if matrix is None:
        matrix = cost_matrix(graph, nodes, [depot, *stops])
    best_cost, best_route = math.inf, None
    for perm in itertools.permutations(stops):
        route = [depot, *perm, depot]
        cost, _ = route_cost(graph, nodes, route, matrix)
        if cost < best_cost:
            best_cost, best_route = cost, route
    return best_route, best_cost


def baseline(graph, nodes, stops, depot='D', matrix=None):
    """Referência: visita os pedidos na ordem em que chegaram (ordem do CSV)."""
    route = [depot, *stops, depot]
    return route, route_cost(graph, nodes, route, matrix)[0]
