"""Тесты выбора версий и получения зависимостей из NuGet."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import nuget
import nuget_source
from errors import AppError
from graph import build_graph
from nuget import Dependency

REPO = "https://api.nuget.org/v3-flatcontainer"
DEPTH = 3
PUBLISHED = {
    "Root": ["1.0.0"],
    "Lib": ["0.9.0", "1.0.0", "1.2.0", "2.0.0-beta"],
    "Base": ["4.0.0", "4.5.0"],
}
PACKAGES = {
    "Root": {"net8.0": [Dependency("Lib", "[1.0.0, )")]},
    "Lib": {"net8.0": [Dependency("Base", "4.5.0")]},
    "Base": {},
}


def fake_versions(repo, name):
    """Возвращает опубликованные версии из подменных данных."""
    return PUBLISHED[name]


def fake_download(repo, name, version):
    """Возвращает зависимости пакета из подменных данных."""
    return PACKAGES[name]


class TestChooseVersion(unittest.TestCase):
    """Тесты выбора версии зависимости по диапазону."""

    def test_lower_bound(self):
        """Нижняя граница берётся из разных записей диапазона."""
        self.assertEqual(nuget.lower_bound("4.5.0"), ("4.5.0", True))
        self.assertEqual(nuget.lower_bound("[1.0, 2.0)"), ("1.0", True))
        self.assertEqual(nuget.lower_bound("(1.0, )"), ("1.0", False))

    def test_lowest_applicable(self):
        """Выбирается наименьшая версия, не ниже нижней границы."""
        versions = PUBLISHED["Lib"]
        self.assertEqual(nuget.choose_version(versions, "1.0"), "1.0.0")
        self.assertEqual(nuget.choose_version(versions, "1.1"), "1.2.0")

    def test_exclusive_bound(self):
        """Невключённая граница пропускает саму версию."""
        versions = PUBLISHED["Lib"]
        self.assertEqual(nuget.choose_version(versions, "(1.0.0, )"),
                         "1.2.0")

    def test_any_version(self):
        """Без указания версии выбирается наименьшая стабильная."""
        versions = PUBLISHED["Lib"]
        self.assertEqual(nuget.choose_version(versions, nuget.ANY_VERSION),
                         "0.9.0")

    def test_no_suitable_version(self):
        """Если подходящей версии нет, возникает ошибка."""
        with self.assertRaises(AppError):
            nuget.choose_version(PUBLISHED["Lib"], "5.0.0")

    def test_version_key(self):
        """Версии сравниваются как числа, а не как строки."""
        self.assertLess(nuget.version_key("1.9.0"),
                        nuget.version_key("1.10.0"))


class TestNugetSource(unittest.TestCase):
    """Тесты построения графа по репозиторию NuGet."""

    def make_graph(self):
        """Строит граф по подменному репозиторию и возвращает источник."""
        with mock.patch.object(nuget_source, "fetch_versions",
                               fake_versions):
            with mock.patch.object(nuget_source, "download_dependencies",
                                   fake_download):
                source = nuget_source.NugetSource(REPO, "Root", "1.0")
                graph = build_graph(source, "Root", DEPTH)
        return source, graph

    def test_graph(self):
        """Транзитивные зависимости попадают в граф."""
        graph = self.make_graph()[1]
        self.assertEqual(graph, {"Root": ["Lib"], "Lib": ["Base"],
                                 "Base": []})

    def test_versions(self):
        """Для каждой зависимости выбрана подходящая версия."""
        source = self.make_graph()[0]
        self.assertEqual(source.label("Lib"), "Lib 1.0.0")
        self.assertEqual(source.label("Base"), "Base 4.5.0")

    def test_groups_saved(self):
        """Прямые зависимости корня сохраняются для вывода по платформам."""
        source = self.make_graph()[0]
        self.assertIn("net8.0", source.groups["Root"])


if __name__ == "__main__":
    unittest.main()
