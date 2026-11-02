"""Тесты ASCII-дерева зависимостей."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tree import CYCLE_MARK, REPEAT_MARK, build_tree

DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}


def as_text(lines):
    """Склеивает строки дерева в текст для сравнения."""
    return [f"{prefix}{name}{mark}" for prefix, name, mark in lines]


class TestTree(unittest.TestCase):
    """Тесты построения ASCII-дерева."""

    def test_diamond(self):
        """Общая зависимость раскрывается один раз, дальше — повтор."""
        self.assertEqual(as_text(build_tree(DIAMOND, "A")), [
            "A",
            "├── B",
            "│   └── D",
            "└── C",
            "    └── D" + REPEAT_MARK,
        ])

    def test_cycle(self):
        """Возврат к пакету на пути от корня помечается как цикл."""
        lines = as_text(build_tree({"A": ["B"], "B": ["A"]}, "A"))
        self.assertEqual(lines, ["A", "└── B", "    └── A" + CYCLE_MARK])

    def test_lonely_root(self):
        """Дерево пакета без зависимостей — одна строка."""
        self.assertEqual(as_text(build_tree({"A": []}, "A")), ["A"])

    def test_boundary(self):
        """Пакет за границей глубины показывается без детей."""
        lines = as_text(build_tree({"A": ["B"]}, "A"))
        self.assertEqual(lines, ["A", "└── B"])


if __name__ == "__main__":
    unittest.main()
