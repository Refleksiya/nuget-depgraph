"""Тесты построения графа зависимостей и поиска циклов."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from file_source import FileSource
from graph import boundary_packages, build_graph, find_cycles

DATA = Path(__file__).parent / "data"
DEPTH = 5


def graph_from_file(name, max_depth):
    """Строит граф для пакета A из файла тестовых данных."""
    source = FileSource(str(DATA / name), "A")
    return build_graph(source, "A", max_depth)


class TestBuildGraph(unittest.TestCase):
    """Тесты обхода графа в ширину."""

    def test_transitive(self):
        """В граф попадают и прямые, и транзитивные зависимости."""
        graph = graph_from_file("graph.txt", DEPTH)
        self.assertEqual(graph, {"A": ["B", "C"], "B": ["D"],
                                 "C": ["D"], "D": []})

    def test_bfs_order(self):
        """Пакеты добавляются в граф по уровням: сначала ближние."""
        graph = graph_from_file("graph.txt", DEPTH)
        self.assertEqual(list(graph), ["A", "B", "C", "D"])

    def test_max_depth(self):
        """Глубже максимальной глубины зависимости не загружаются."""
        graph = graph_from_file("chain.txt", 2)
        self.assertEqual(list(graph), ["A", "B"])
        self.assertEqual(boundary_packages(graph), ["C"])

    def test_depth_one(self):
        """При глубине 1 загружаются только прямые зависимости."""
        graph = graph_from_file("graph.txt", 1)
        self.assertEqual(graph, {"A": ["B", "C"]})

    def test_cycle_terminates(self):
        """Цикл не приводит к бесконечному обходу."""
        graph = graph_from_file("cycle.txt", DEPTH)
        self.assertEqual(list(graph), ["A", "B", "C", "D"])


class TestCycles(unittest.TestCase):
    """Тесты поиска циклических зависимостей."""

    def test_cycle_found(self):
        """Цикл A -> B -> C -> A находится."""
        graph = graph_from_file("cycle.txt", DEPTH)
        self.assertEqual(find_cycles(graph, "A"), [["A", "B", "C", "A"]])

    def test_no_cycles(self):
        """В графе без циклов ничего не находится."""
        graph = graph_from_file("graph.txt", DEPTH)
        self.assertEqual(find_cycles(graph, "A"), [])

    def test_self_loop(self):
        """Пакет, зависящий сам от себя, — тоже цикл."""
        self.assertEqual(find_cycles({"A": ["A"]}, "A"), [["A", "A"]])


if __name__ == "__main__":
    unittest.main()
