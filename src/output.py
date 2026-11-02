"""Вывод результатов работы приложения на экран."""

from config import describe
from graph import boundary_packages, find_cycles
from nuget import unique_dependencies

NO_DEPENDENCIES = "зависимостей нет"
LEAF = "нет зависимостей"
LINE_WIDTH = 78
FIRST_INDENT = "  "
NEXT_INDENT = "      "


def wrap_items(items, width):
    """Разбивает список подписей на строки не длиннее width символов."""
    lines = []
    current = ""
    for item in items:
        candidate = f"{current}, {item}" if current else item
        if current and len(candidate) > width:
            lines.append(current + ",")
            current = item
        else:
            current = candidate
    lines.append(current)
    return lines


def print_items(head, items):
    """Выводит заголовок и список подписей, перенося целые подписи."""
    one_line = FIRST_INDENT + head + ", ".join(items)
    if len(one_line) <= LINE_WIDTH:
        print(one_line)
        return
    if head:
        print(FIRST_INDENT + head.rstrip())
    for line in wrap_items(items, LINE_WIDTH - len(NEXT_INDENT)):
        print(NEXT_INDENT + line)


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
        print(f"  {NO_DEPENDENCIES}")
        return
    for framework, dependencies in groups.items():
        print(f"  [{framework}]")
        if not dependencies:
            print(f"    {NO_DEPENDENCIES}")
        for dependency in dependencies:
            print(f"    {format_dependency(dependency)}")
    names = unique_dependencies(groups)
    print(f"\nВсего различных прямых зависимостей: {len(names)}")
    for name in names:
        print(f"  {name}")


def print_edges(source, name, dependencies):
    """Выводит строку «пакет -> его зависимости»."""
    head = f"{source.label(name)} -> "
    if not dependencies:
        print(FIRST_INDENT + head + LEAF)
        return
    print_items(head, [source.label(item) for item in dependencies])


def print_cycles(graph, root):
    """Выводит найденные циклические зависимости."""
    cycles = find_cycles(graph, root)
    if not cycles:
        print("Циклические зависимости: не найдены")
        return
    print("Циклические зависимости:")
    for cycle in cycles:
        print(f"  {' -> '.join(cycle)}")


def print_graph(source, graph, config):
    """Выводит граф зависимостей, пакеты на границе глубины и циклы."""
    print(f"\nГраф зависимостей (BFS, максимальная глубина "
          f"{config.depth}):")
    for name, dependencies in graph.items():
        print_edges(source, name, dependencies)
    boundary = boundary_packages(graph)
    print(f"Всего пакетов в графе: {len(graph) + len(boundary)}")
    if boundary:
        labels = [source.label(name) for name in boundary]
        print("Зависимости не загружались (достигнута максимальная "
              "глубина):")
        print_items("", labels)
    print_cycles(graph, config.package)
