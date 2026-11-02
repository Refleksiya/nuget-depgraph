"""Точка входа инструмента визуализации графа зависимостей."""

import sys

from config import build_config
from errors import AppError
from file_source import FileSource
from graph import build_graph
from nuget_source import NugetSource
from output import print_config, print_dependencies, print_graph

EXIT_OK = 0
EXIT_ERROR = 1


def make_source(config):
    """Выбирает источник зависимостей: тестовый файл или репозиторий."""
    if config.test_repo:
        return FileSource(config.repo, config.package)
    return NugetSource(config.repo, config.package, config.version)


def print_results(config, source, graph):
    """Выводит прямые зависимости и граф зависимостей."""
    if not config.test_repo:
        print_dependencies(config, source.groups[config.package])
    print_graph(source, graph, config)


def run(argv):
    """Выполняет работу приложения и возвращает код возврата."""
    try:
        config = build_config(argv)
        print_config(config)
        source = make_source(config)
        graph = build_graph(source, config.package, config.depth)
    except AppError as error:
        sys.stdout.flush()
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print_results(config, source, graph)
    return EXIT_OK


def main():
    """Запускает приложение с аргументами командной строки."""
    return run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
