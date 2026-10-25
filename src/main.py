"""Точка входа инструмента визуализации графа зависимостей."""

import sys

from config import build_config, describe
from errors import AppError
from nuget import get_direct_dependencies, unique_dependencies

EXIT_OK = 0
EXIT_ERROR = 1
TEST_MODE_NOTE = "Тестовый репозиторий будет разобран на этапе 3."


def print_config(config):
    """Выводит все параметры запуска в формате ключ-значение."""
    print("Параметры запуска:")
    for line in describe(config):
        print(f"  {line}")


def format_dependency(dependency):
    """Готовит строку с именем зависимости и её версиями."""
    return f"{dependency.name} (версия: {dependency.version})"


def print_dependencies(config, groups):
    """Выводит прямые зависимости по платформам и общий список."""
    print(f"\nПрямые зависимости {config.package} {config.version}:")
    if not groups:
        print("  зависимостей нет")
        return
    for framework, dependencies in groups.items():
        print(f"  [{framework}]")
        if not dependencies:
            print("    зависимостей нет")
        for dependency in dependencies:
            print(f"    {format_dependency(dependency)}")
    names = unique_dependencies(groups)
    print(f"\nВсего различных прямых зависимостей: {len(names)}")
    for name in names:
        print(f"  {name}")


def run(argv):
    """Выполняет работу приложения и возвращает код возврата."""
    try:
        config = build_config(argv)
        print_config(config)
        if config.test_repo:
            print(TEST_MODE_NOTE)
            return EXIT_OK
        groups = get_direct_dependencies(
            config.repo, config.package, config.version
        )
    except AppError as error:
        sys.stdout.flush()
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print_dependencies(config, groups)
    return EXIT_OK


def main():
    """Запускает приложение с аргументами командной строки."""
    return run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
