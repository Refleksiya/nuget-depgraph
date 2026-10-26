"""Тесты разбора и проверки параметров командной строки."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import DEFAULT_REPO, build_config, describe
from errors import AppError

GRAPH = str(Path(__file__).parent / "data" / "graph.txt")


def default_config():
    """Создаёт конфигурацию с минимальным набором параметров."""
    return build_config(["--package", "Serilog", "--version", "3.1.1"])


class TestDefaults(unittest.TestCase):
    """Тесты значений по умолчанию."""

    def test_repo(self):
        """Без параметра используется адрес репозитория NuGet."""
        self.assertEqual(default_config().repo, DEFAULT_REPO)

    def test_depth(self):
        """Глубина по умолчанию равна трём."""
        self.assertEqual(default_config().depth, 3)

    def test_flags(self):
        """Режимы выключены, пока их не включил пользователь."""
        config = default_config()
        self.assertFalse(config.test_repo)
        self.assertFalse(config.tree)

    def test_describe(self):
        """Описание содержит строку с именем пакета."""
        self.assertIn("package = Serilog", describe(default_config()))


class TestValues(unittest.TestCase):
    """Тесты разбора заданных пользователем значений."""

    def test_all_options(self):
        """Все параметры принимаются вместе."""
        config = build_config([
            "--package", "A", "--test-repo", "--repo", GRAPH,
            "--tree", "--max-depth", "5",
        ])
        self.assertEqual(config.package, "A")
        self.assertEqual(config.depth, 5)
        self.assertTrue(config.tree)

    def test_version_optional_in_test_mode(self):
        """В тестовом режиме версия не обязательна."""
        config = build_config(["--package", "A", "--test-repo",
                               "--repo", GRAPH])
        self.assertEqual(config.version, "")

    def test_prerelease_version(self):
        """Версия с предварительным выпуском принимается."""
        config = build_config(["--package", "A", "--version", "2.0.0-beta1"])
        self.assertEqual(config.version, "2.0.0-beta1")


class TestErrors(unittest.TestCase):
    """Тесты обработки ошибок в параметрах."""

    def check(self, argv):
        """Проверяет, что набор параметров вызывает ошибку."""
        with self.assertRaises(AppError):
            build_config(argv)

    def test_no_package(self):
        """Имя пакета обязательно."""
        self.check(["--version", "1.0.0"])

    def test_bad_package(self):
        """Имя пакета с пробелом не принимается."""
        self.check(["--package", "bad name", "--version", "1.0.0"])

    def test_no_version(self):
        """Версия обязательна при работе с реальным репозиторием."""
        self.check(["--package", "Serilog"])

    def test_bad_version(self):
        """Версия из букв не принимается."""
        self.check(["--package", "Serilog", "--version", "последняя"])

    def test_bad_repo(self):
        """Адрес репозитория без http не принимается."""
        self.check(["--package", "A", "--version", "1.0", "--repo", "nuget"])

    def test_missing_file(self):
        """Отсутствующий файл тестового репозитория — ошибка."""
        self.check(["--package", "A", "--test-repo", "--repo", "nope.txt"])

    def test_depth_not_number(self):
        """Глубина должна быть числом."""
        self.check(["--package", "A", "--version", "1.0",
                    "--max-depth", "много"])

    def test_depth_out_of_range(self):
        """Глубина вне допустимого диапазона — ошибка."""
        self.check(["--package", "A", "--version", "1.0",
                    "--max-depth", "0"])
        self.check(["--package", "A", "--version", "1.0",
                    "--max-depth", "50"])


if __name__ == "__main__":
    unittest.main()
