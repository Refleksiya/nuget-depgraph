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

GRAPH = str(Path(__file__).parent / "data" / "graph.txt")


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
        """В тестовом режиме выводятся параметры и код 0."""
        code, output = run_quietly(["--package", "A", "--test-repo",
                                    "--repo", GRAPH])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("package = A", output)

    def test_dependencies_printed(self):
        """Прямые зависимости выводятся на экран."""
        groups = {"net8.0": [Dependency("First", "1.0.0")]}
        with mock.patch.object(main, "get_direct_dependencies",
                               return_value=groups):
            code, output = run_quietly(["--package", "Demo",
                                        "--version", "1.0.0"])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("[net8.0]", output)
        self.assertIn("First (версия: 1.0.0)", output)

    def test_no_dependencies(self):
        """Для пакета без зависимостей выводится сообщение."""
        with mock.patch.object(main, "get_direct_dependencies",
                               return_value={}):
            code, output = run_quietly(["--package", "Demo",
                                        "--version", "1.0.0"])
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("зависимостей нет", output)


if __name__ == "__main__":
    unittest.main()
