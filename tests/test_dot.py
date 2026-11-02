"""Тесты описания графа на языке Graphviz."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dot import quote, to_dot


class NameSource:
    """Подменный источник: подпись пакета — его имя."""

    def label(self, name):
        """Возвращает имя пакета без изменений."""
        return name


class TestDot(unittest.TestCase):
    """Тесты построения текста на языке DOT."""

    def test_quote(self):
        """Имя заключается в кавычки, кавычки внутри экранируются."""
        self.assertEqual(quote('a"b'), '"a\\"b"')

    def test_edges(self):
        """Каждая зависимость становится ребром графа."""
        lines = to_dot(NameSource(), {"A": ["B", "C"], "B": []}, "A")
        self.assertEqual(lines[0], 'digraph "A" {')
        self.assertIn('    "A" -> "B";', lines)
        self.assertIn('    "A" -> "C";', lines)
        self.assertEqual(lines[-1], "}")

    def test_cycle_edge(self):
        """Ребро цикла тоже попадает в описание."""
        lines = to_dot(NameSource(), {"A": ["B"], "B": ["A"]}, "A")
        self.assertIn('    "B" -> "A";', lines)

    def test_boundary_dashed(self):
        """Пакет на границе глубины рисуется пунктиром."""
        lines = to_dot(NameSource(), {"A": ["B"]}, "A")
        self.assertIn('    "B" [style=dashed];', lines)

    def test_lonely_root(self):
        """Пакет без зависимостей всё равно виден на графе."""
        lines = to_dot(NameSource(), {"A": []}, "A")
        self.assertIn('    "A";', lines)


if __name__ == "__main__":
    unittest.main()
