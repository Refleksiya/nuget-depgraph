"""Построение графа зависимостей и поиск циклических зависимостей."""


def visit_level(source, level, depth, graph, max_depth):
    """Обходит один уровень графа и рекурсивно переходит к следующему.

    level — пакеты текущего уровня, depth — их расстояние от корня.
    Зависимости загружаются только у пакетов, которые ближе к корню,
    чем максимальная глубина.
    """
    if not level or depth >= max_depth:
        return
    next_level = []
    for name in level:
        graph[name] = source.dependencies(name)
        for dependency in graph[name]:
            seen = dependency in graph or dependency in level
            if not seen and dependency not in next_level:
                next_level.append(dependency)
    visit_level(source, next_level, depth + 1, graph, max_depth)


def build_graph(source, root, max_depth):
    """Строит граф зависимостей обходом в ширину (BFS) с рекурсией.

    Возвращает словарь: пакет -> список его прямых зависимостей.
    Каждый пакет загружается один раз, поэтому циклы не приводят
    к бесконечной работе.
    """
    graph = {}
    visit_level(source, [root], 0, graph, max_depth)
    return graph


def boundary_packages(graph):
    """Возвращает пакеты, зависимости которых не загружались из-за глубины."""
    result = []
    for dependencies in graph.values():
        for name in dependencies:
            if name not in graph and name not in result:
                result.append(name)
    return result


def search_cycles(graph, name, path, done, cycles):
    """Обходит граф в глубину и запоминает найденные циклы."""
    path.append(name)
    for dependency in graph.get(name, []):
        if dependency in path:
            start = path.index(dependency)
            cycles.append(path[start:] + [dependency])
        elif dependency not in done:
            search_cycles(graph, dependency, path, done, cycles)
    path.pop()
    done.add(name)


def find_cycles(graph, root):
    """Находит циклические зависимости, достижимые из корневого пакета."""
    cycles = []
    search_cycles(graph, root, [], set(), cycles)
    return cycles


def visit_for_order(graph, name, visiting, order):
    """Добавляет в порядок загрузки сначала зависимости, затем сам пакет.

    visiting — пакеты, обход которых ещё не закончен. Если пакет
    встретился повторно, пока его обход не закончен, это цикл, и
    повторный вход пропускается.
    """
    if name in order or name in visiting:
        return
    visiting.add(name)
    for dependency in graph.get(name, []):
        visit_for_order(graph, dependency, visiting, order)
    visiting.remove(name)
    order.append(name)


def load_order(graph, root):
    """Возвращает порядок загрузки: зависимости раньше пакетов.

    Анализируемый пакет загружается последним.
    """
    order = []
    visit_for_order(graph, root, set(), order)
    return order
