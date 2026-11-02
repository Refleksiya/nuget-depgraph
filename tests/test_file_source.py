"""Тесты чтения файла тестового репозитория."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from errors import AppError
from file_source import FileSource, parse_line, read_graph_file

DATA = Path(__file__).parent / "data"


class TestFileSource(unittest.TestCase):
    """Тесты разбора описания графа."""

    def test_parse_line(self):
        """Строка делится на пакет и его зависимости."""
        self.assertEqual(parse_line("A: B C\n", 1), ("A", ["B", "C"]))

    def test_no_dependencies(self):
        """Пакет без зависимостей описывается пустой правой частью."""
        self.assertEqual(parse_line("D:", 1), ("D", []))

    def test_read_file(self):
        """Файл читается в словарь пакет -> зависимости."""
        graph = read_graph_file(str(DATA / "graph.txt"))
        self.assertEqual(graph["A"], ["B", "C"])

    def test_lowercase_name(self):
        """Имя из маленьких букв вызывает ошибку."""
        with self.assertRaises(AppError):
            read_graph_file(str(DATA / "bad_name.txt"))

    def test_no_separator(self):
        """Строка без двоеточия вызывает ошибку."""
        with self.assertRaises(AppError):
            read_graph_file(str(DATA / "bad_line.txt"))

    def test_repeated_package(self):
        """Повторное описание пакета вызывает ошибку."""
        with self.assertRaises(AppError):
            read_graph_file(str(DATA / "repeated.txt"))

    def test_unknown_root(self):
        """Корневой пакет должен быть описан в файле."""
        with self.assertRaises(AppError):
            FileSource(str(DATA / "graph.txt"), "Z")

    def test_undescribed_dependency(self):
        """У пакета, не описанного в файле, зависимостей нет."""
        source = FileSource(str(DATA / "graph.txt"), "A")
        self.assertEqual(source.dependencies("Z"), [])


if __name__ == "__main__":
    unittest.main()
