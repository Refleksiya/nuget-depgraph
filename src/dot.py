"""Текстовое представление графа зависимостей на языке Graphviz (DOT)."""

from graph import boundary_packages

INDENT = "    "


def quote(text):
    """Заключает имя в кавычки, как требует язык DOT."""
    return '"' + text.replace('"', '\\"') + '"'


def edge_lines(source, graph):
    """Готовит строки рёбер «пакет -> зависимость»."""
    lines = []
    for name, dependencies in graph.items():
        for dependency in dependencies:
            start = quote(source.label(name))
            end = quote(source.label(dependency))
            lines.append(f"{INDENT}{start} -> {end};")
    return lines


def to_dot(source, graph, root):
    """Возвращает описание графа на языке DOT в виде списка строк.

    Пакеты, зависимости которых не загружались из-за максимальной
    глубины, рисуются пунктиром.
    """
    lines = [f"digraph {quote(root)} {{"]
    if not graph.get(root):
        lines.append(f"{INDENT}{quote(source.label(root))};")
    lines.extend(edge_lines(source, graph))
    for name in boundary_packages(graph):
        lines.append(f"{INDENT}{quote(source.label(name))} [style=dashed];")
    lines.append("}")
    return lines
