"""Источник зависимостей: файл тестового репозитория.

Каждая строка файла описывает один пакет и его прямые зависимости:

    A: B C
    B: D
    D:

Пакеты называются большими латинскими буквами.
"""

import re

from errors import AppError

NAME_PATTERN = re.compile(r"^[A-Z]+$")
SEPARATOR = ":"


def check_name(name, line_number):
    """Проверяет, что имя пакета состоит из больших латинских букв."""
    if not NAME_PATTERN.match(name):
        raise AppError(
            f"строка {line_number}: имя пакета должно состоять "
            f"из больших латинских букв: {name}"
        )
    return name


def parse_line(line, line_number):
    """Разбирает строку вида «A: B C» на пакет и список зависимостей."""
    name, separator, rest = line.partition(SEPARATOR)
    if not separator:
        raise AppError(f"строка {line_number}: нет двоеточия после имени")
    package = check_name(name.strip(), line_number)
    dependencies = [check_name(item, line_number) for item in rest.split()]
    return package, dependencies


def read_lines(path):
    """Читает все строки файла тестового репозитория."""
    try:
        with open(path, encoding="utf-8") as file:
            return file.readlines()
    except (OSError, UnicodeDecodeError) as error:
        raise AppError(f"не удалось прочитать файл {path}: {error}")


def read_graph_file(path):
    """Читает файл тестового репозитория в словарь пакет -> зависимости."""
    graph = {}
    for line_number, line in enumerate(read_lines(path), start=1):
        if not line.strip():
            continue
        package, dependencies = parse_line(line, line_number)
        if package in graph:
            raise AppError(
                f"строка {line_number}: пакет {package} описан повторно"
            )
        graph[package] = dependencies
    return graph


class FileSource:
    """Получает зависимости пакетов из файла тестового репозитория."""

    def __init__(self, path, package):
        """Читает файл и проверяет, что в нём описан корневой пакет."""
        self.graph = read_graph_file(path)
        if package not in self.graph:
            raise AppError(f"пакет {package} не описан в файле {path}")

    def dependencies(self, name):
        """Возвращает прямые зависимости пакета из файла."""
        return self.graph.get(name, [])

    def label(self, name):
        """Возвращает подпись пакета: в тестовом режиме это его имя."""
        return name
