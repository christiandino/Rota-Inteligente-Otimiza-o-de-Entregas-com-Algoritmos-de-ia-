import math
import tempfile
import unittest
from pathlib import Path

from src.core import (astar, baseline, bfs, dfs, dijkstra, kmeans, load_data,
                      optimize_route)
from src.main import ROOT, run


class TestAlgorithms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.graph, cls.deliveries = load_data(ROOT / 'data')

    def test_astar_dijkstra_all_pairs(self):
        for a in self.nodes:
            for b in self.nodes:
                path, c = astar(self.graph, self.nodes, a, b)
                _, d = dijkstra(self.graph, a, b)
                self.assertAlmostEqual(c, d)
                self.assertEqual(path[0], a)
                self.assertEqual(path[-1], b)

    def test_astar_expands_no_more_than_dijkstra(self):
        for a in self.nodes:
            for b in self.nodes:
                sa, sd = {}, {}
                astar(self.graph, self.nodes, a, b, stats=sa)
                dijkstra(self.graph, a, b, stats=sd)
                self.assertLessEqual(sa['expandidos'], sd['expandidos'])

    def test_bfs_min_hops(self):
        g = {'a': {'b': 100, 'c': 1}, 'b': {'d': 1}, 'c': {'e': 1}, 'e': {'d': 1}, 'd': {}}
        self.assertEqual(bfs(g, 'a', 'd')[1], 101)
        self.assertEqual(dijkstra(g, 'a', 'd')[1], 3)

    def test_dfs_finds_valid_path(self):
        path, cost = dfs(self.graph, 'D', 'N44')
        self.assertEqual((path[0], path[-1]), ('D', 'N44'))
        self.assertGreaterEqual(cost, dijkstra(self.graph, 'D', 'N44')[1])

    def test_unreachable(self):
        g = {'a': {}, 'b': {}}
        n = {'a': (0, 0), 'b': (1, 0)}
        self.assertEqual(astar(g, n, 'a', 'b'), ([], math.inf))
        self.assertEqual(dijkstra(g, 'a', 'b'), ([], math.inf))
        self.assertEqual(bfs(g, 'a', 'b'), ([], math.inf))
        self.assertEqual(dfs(g, 'a', 'b'), ([], math.inf))

    def test_same_node(self):
        self.assertEqual(astar(self.graph, self.nodes, 'D', 'D'), (['D'], 0))

    def test_clustering(self):
        groups = kmeans(self.nodes, self.deliveries, 2)
        self.assertEqual(sorted(sum(groups, [])), sorted(self.deliveries))
        self.assertTrue(all(groups))

    def test_invalid_k(self):
        with self.assertRaises(ValueError):
            kmeans(self.nodes, self.deliveries, 0)
        with self.assertRaises(ValueError):
            kmeans(self.nodes, self.deliveries, len(self.deliveries) + 1)

    def test_optimal_never_worse(self):
        for g in kmeans(self.nodes, self.deliveries, 2):
            self.assertLessEqual(optimize_route(self.graph, self.nodes, g)[1],
                                 baseline(self.graph, self.nodes, g)[1])

    def test_empty_group(self):
        self.assertEqual(optimize_route(self.graph, self.nodes, []), (['D', 'D'], 0))

    def test_too_many_stops(self):
        with self.assertRaises(ValueError):
            optimize_route(self.graph, self.nodes, list(self.nodes)[1:11])

    def test_invalid_node(self):
        with self.assertRaises(ValueError):
            astar(self.graph, self.nodes, 'unknown', 'D')


class TestPipeline(unittest.TestCase):
    """Executa o pipeline em pasta temporária para não sobrescrever outputs/ versionado."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_full_pipeline(self):
        out = run(2, self.out, quiet=True)
        self.assertEqual(out['entregas_total'], 8)
        self.assertTrue((self.out / 'resultados.json').exists())
        self.assertTrue((self.out / 'mapa_rotas.svg').exists())
        self.assertLessEqual(out['tempo_total_otimizado_min'], out['tempo_total_base_min'])

    def test_one_to_three_drivers(self):
        for k in (1, 2, 3):
            out = run(k, self.out, quiet=True)
            self.assertEqual(out['entregadores'], k)
            self.assertEqual(sum(len(r['entregas']) for r in out['rotas']), 8)


if __name__ == '__main__':
    unittest.main()
