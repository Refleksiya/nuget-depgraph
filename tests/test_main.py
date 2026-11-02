"""Тесты точки входа приложения."""

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import main
from nuget import Dependency

DATA = Path(__file__).parent / "data"
GRAPH = str(DATA / "graph.txt")
CYCLE = str(DATA / "cycle.txt")


class FakeSource:
    """Подменный репозиторий NuGet из одного пакета с одной зависимостью."""

    def __init__(self, repo, package, version):
        """Запоминает корневой пакет и его зависимости по платформам."""
        self.groups = {package: {"net8.0": [Dependency("First", "1.0.0")]}}

    def dependencies(self, name):
        """Возвращает зависимости: у First их нет."""
        if name == "First":
            return []
        return ["First"]

    def label(self, name):
        """Возвращает подпись пакета с условной версией."""
        return f"{name} 1.0.0"


def run_quietly(argv):
    """Запускает приложение и возвращает код возврата и вывод."""
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        with contextlib.redirect_stderr(output):
            code = main.run(argv)
    return code, output.getvalue()


class TestRun(unittest.TestCase):
    """Тесты запуска приложения целиком."""

    def test_error_code(self):
        """При ошибке в параметрах возвращается код 1."""
        code, output = run_quietly(["--version", "1.0.0"])
        self.assertEqual(code, main.EXIT_ERROR)
        self.assertIn("Ошибка", output)

    def test_test_mode(self):
        """В тестовом режиме выводится граф из файла."""
        code, output = run_quietly(["--package", "A", "--test-repo",
                                    "--repo", GRAPH])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("package = A", output)
        self.assertIn("A -> B, C", output)
        self.assertIn("не найдены", output)

    def test_cycle_printed(self):
        """Найденный цикл выводится на экран."""
        code, output = run_quietly(["--package", "A", "--test-repo",
                                    "--repo", CYCLE])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("A -> B -> C -> A", output)

    def test_unknown_test_package(self):
        """Пакет, которого нет в тестовом файле, вызывает ошибку."""
        code, output = run_quietly(["--package", "Z", "--test-repo",
                                    "--repo", GRAPH])
        self.assertEqual(code, main.EXIT_ERROR)
        self.assertIn("не описан", output)

    def test_order_mode(self):
        """В режиме порядка загрузки выводится нумерованный список."""
        code, output = run_quietly(["--package", "A", "--test-repo",
                                    "--repo", GRAPH, "--order"])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("1. D", output)
        self.assertIn("4. A", output)
        self.assertNotIn("Граф зависимостей", output)

    def test_order_with_cycle(self):
        """При цикле порядок выводится вместе с найденным циклом."""
        code, output = run_quietly(["--package", "A", "--test-repo",
                                    "--repo", CYCLE, "--order"])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("A -> B -> C -> A", output)

    def test_graphviz_printed(self):
        """В режиме графа выводится описание на языке Graphviz."""
        code, output = run_quietly(["--package", "A", "--test-repo",
                                    "--repo", GRAPH])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn('digraph "A" {', output)
        self.assertIn('"A" -> "B";', output)
        self.assertNotIn("Дерево зависимостей", output)

    def test_tree_printed(self):
        """С параметром --tree выводится ASCII-дерево."""
        code, output = run_quietly(["--package", "A", "--test-repo",
                                    "--repo", GRAPH, "--tree"])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("├── B", output)
        self.assertIn("└── D (повтор)", output)

    def test_nuget_mode(self):
        """В режиме NuGet выводятся прямые зависимости и граф."""
        with mock.patch.object(main, "NugetSource", FakeSource):
            code, output = run_quietly(["--package", "Demo",
                                        "--version", "1.0.0"])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("First (версия: 1.0.0)", output)
        self.assertIn("Demo 1.0.0 -> First 1.0.0", output)


if __name__ == "__main__":
    unittest.main()
