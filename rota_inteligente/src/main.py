"""Execução do projeto Rota Inteligente (Sabor Express).

Uso (a partir da raiz do projeto):
    python -m src.main --entregadores 2
"""
import argparse
import json
import math
from pathlib import Path

from .core import (MAX_STOPS, astar, baseline, bfs, cost_matrix, dfs, dijkstra,
                   heuristic_scale, inertia, kmeans, load_data, optimize_route,
                   route_cost)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'outputs'
PALETTE = ['#d14d72', '#2576c7', '#27936c', '#a87322', '#7c3aed', '#0e7490']


def svg_map(nodes, graph, deliveries, paths, file):
    """Gera o diagrama do grafo (ruas com pesos) e os trajetos de cada entregador."""
    W, H = 780, 560

    def xy(n):
        return 70 + nodes[n][0] * 95, 470 - nodes[n][1] * 85

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="#f6f8fc"/>'
           '<text x="30" y="32" font-size="22" font-family="Arial" fill="#163a63">'
           'Sabor Express | Grafo simulado e rotas otimizadas</text>']

    drawn = set()
    for a, adj in graph.items():
        for b, w in adj.items():
            if (b, a) in drawn:
                continue
            drawn.add((a, b))
            (x, y), (u, v) = xy(a), xy(b)
            out.append(f'<line x1="{x}" y1="{y}" x2="{u}" y2="{v}" stroke="#c2cad5" stroke-width="3"/>')
            mx, my = (x + u) / 2, (y + v) / 2
            out.append(f'<text x="{mx + 6 if x == u else mx}" y="{my + 16 if y == v else my + 4}" '
                       f'font-family="Arial" font-size="11" fill="#8a94a6" '
                       f'text-anchor="{"start" if x == u else "middle"}">{w:g}</text>')

    for j, route in enumerate(paths):
        color = PALETTE[j % len(PALETTE)]
        for a, b in zip(route, route[1:]):
            (x, y), (u, v) = xy(a), xy(b)
            out.append(f'<line x1="{x}" y1="{y}" x2="{u}" y2="{v}" stroke="{color}" '
                       'stroke-width="5" stroke-linecap="round" opacity=".8"/>')

    for n in nodes:
        x, y = xy(n)
        color = '#f0a22b' if n == 'D' else ('#2563eb' if n in deliveries else '#64748b')
        out.append(f'<circle cx="{x}" cy="{y}" r="12" fill="{color}" stroke="white" stroke-width="2"/>'
                   f'<text x="{x + 15}" y="{y - 12}" font-family="Arial" font-size="14" '
                   f'fill="#1c2938">{n}</text>')

    # Legenda
    lx, ly = 560, 110
    items = [('#f0a22b', 'circle', 'Depósito (D)'), ('#2563eb', 'circle', 'Ponto de entrega'),
             ('#64748b', 'circle', 'Cruzamento')]
    items += [(PALETTE[j % len(PALETTE)], 'line', f'Entregador {j + 1}') for j in range(len(paths))]
    out.append(f'<text x="{lx}" y="{ly - 20}" font-family="Arial" font-size="15" '
               'font-weight="bold" fill="#163a63">Legenda</text>')
    for i, (color, kind, label) in enumerate(items):
        yy = ly + i * 26
        if kind == 'circle':
            out.append(f'<circle cx="{lx + 10}" cy="{yy}" r="8" fill="{color}"/>')
        else:
            out.append(f'<line x1="{lx}" y1="{yy}" x2="{lx + 22}" y2="{yy}" stroke="{color}" '
                       'stroke-width="5" stroke-linecap="round"/>')
        out.append(f'<text x="{lx + 32}" y="{yy + 5}" font-family="Arial" font-size="13" '
                   f'fill="#1c2938">{label}</text>')
    out.append('<text x="30" y="530" font-family="Arial" font-size="13" fill="#45556c">'
               'Números nas ruas = tempo estimado em minutos (dados fictícios). '
               'Vias de mão dupla.</text></svg>')
    Path(file).write_text(''.join(out), encoding='utf-8')


def compare_searches(graph, nodes, pairs):
    """Compara A*, Dijkstra, BFS e DFS: custo, caminho e nós expandidos."""
    scale = heuristic_scale(graph, nodes)
    rows = []
    for a, b in pairs:
        sa, sd = {}, {}
        ap, ac = astar(graph, nodes, a, b, stats=sa, scale=scale)
        dp, dc = dijkstra(graph, a, b, stats=sd)
        bp, bc = bfs(graph, a, b)
        fp, fc = dfs(graph, a, b)
        rows.append({'origem': a, 'destino': b,
                     'astar_min': ac, 'dijkstra_min': dc, 'bfs_min': bc, 'dfs_min': fc,
                     'astar_nos_expandidos': sa['expandidos'],
                     'dijkstra_nos_expandidos': sd['expandidos'],
                     'astar_caminho': ap, 'dijkstra_caminho': dp,
                     'bfs_caminho': bp, 'dfs_caminho': fp})
    return rows


def run(k, out_dir=None, quiet=False, depot='D'):
    out_dir = Path(out_dir) if out_dir else DEFAULT_OUT
    out_dir.mkdir(parents=True, exist_ok=True)

    nodes, graph, deliveries = load_data(ROOT / 'data')
    if len(deliveries) != len(set(deliveries)):
        raise ValueError('Entregas duplicadas não suportadas nesta demonstração')
    groups = kmeans(nodes, deliveries, k)
    if any(len(g) > MAX_STOPS for g in groups):
        raise ValueError(f'Aumente o número de entregadores (máximo {MAX_STOPS} paradas por grupo)')

    # A* calculado uma única vez para cada par depósito/entrega (reutilizado nas permutações)
    matrix = cost_matrix(graph, nodes, [depot, *deliveries])

    rotas, paths = [], []
    base_total = opt_total = 0
    for i, g in enumerate(groups, 1):
        base, bc = baseline(graph, nodes, g, depot, matrix)
        route, oc = optimize_route(graph, nodes, g, depot, matrix)
        if not math.isfinite(oc):
            raise ValueError('Grafo desconectado para as entregas')
        _, segments = route_cost(graph, nodes, route, matrix)
        flat = [n for seg in segments for n in seg[:-1]] + [segments[-1][-1]] if segments else []
        paths.append(flat)
        base_total += bc
        opt_total += oc
        rotas.append({'entregador': i, 'entregas': g,
                      'rota_base': base, 'rota_otimizada': route,
                      'tempo_base_min': round(bc, 2), 'tempo_otimizado_min': round(oc, 2),
                      'economia_min': round(bc - oc, 2), 'caminho_completo': flat})

    pairs = [(depot, deliveries[0]), (depot, deliveries[-1]), (deliveries[0], deliveries[-1])]
    output = {
        'cenario': 'Dados fictícios; pesos em minutos; vias conforme edges.csv',
        'entregadores': k,
        'entregas_total': len(deliveries),
        'inercia_kmeans': round(inertia(nodes, groups), 3),
        'rotas': rotas,
        'tempo_total_base_min': round(base_total, 2),
        'tempo_total_otimizado_min': round(opt_total, 2),
        'economia_percentual': round(100 * (base_total - opt_total) / base_total, 2) if base_total else 0,
        'maior_rota_min': round(max(r['tempo_otimizado_min'] for r in rotas), 2),
        'comparacao_buscas': compare_searches(graph, nodes, pairs),
        'observacao': ('Tempo total = soma dos tempos de todos os entregadores (minutos-entregador); '
                       'maior_rota_min = tempo até o último entregador voltar. '
                       'Não inclui preparo, atendimento ou trânsito em tempo real.'),
    }
    (out_dir / 'resultados.json').write_text(json.dumps(output, indent=2, ensure_ascii=False),
                                             encoding='utf-8')
    svg_map(nodes, graph, deliveries, paths, out_dir / 'mapa_rotas.svg')
    if not quiet:
        print_summary(output, out_dir)
    return output


def print_summary(o, out_dir):
    print(f"\n=== Rota Inteligente | Sabor Express | {o['entregadores']} entregador(es) ===")
    for r in o['rotas']:
        print(f"\nEntregador {r['entregador']}: pedidos {', '.join(r['entregas'])}")
        print(f"  Ordem original : {' -> '.join(r['rota_base'])}  ({r['tempo_base_min']:g} min)")
        print(f"  Ordem otimizada: {' -> '.join(r['rota_otimizada'])}  ({r['tempo_otimizado_min']:g} min)")
    print(f"\nTempo total (baseline) : {o['tempo_total_base_min']:g} min")
    print(f"Tempo total (otimizado): {o['tempo_total_otimizado_min']:g} min")
    print(f"Economia               : {o['economia_percentual']:g}%")
    print(f"Maior rota individual  : {o['maior_rota_min']:g} min")
    print('\nComparação de buscas (custo em minutos | nós expandidos):')
    for c in o['comparacao_buscas']:
        print(f"  {c['origem']}->{c['destino']}: A* {c['astar_min']:g} ({c['astar_nos_expandidos']} nós) | "
              f"Dijkstra {c['dijkstra_min']:g} ({c['dijkstra_nos_expandidos']} nós) | "
              f"BFS {c['bfs_min']:g} | DFS {c['dfs_min']:g}")
    print(f"\nArquivos gerados: {out_dir / 'resultados.json'} e {out_dir / 'mapa_rotas.svg'}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Otimização de entregas Sabor Express')
    parser.add_argument('--entregadores', type=int, default=2, help='número de grupos/entregadores (padrão: 2)')
    parser.add_argument('--saida', default=None, help='pasta de saída (padrão: outputs/)')
    args = parser.parse_args()
    try:
        run(args.entregadores, args.saida)
    except (ValueError, FileNotFoundError) as e:
        parser.error(str(e))
