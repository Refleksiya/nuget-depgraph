"""Представление зависимостей в виде ASCII-дерева."""

BRANCH = "├── "
LAST_BRANCH = "└── "
PIPE = "│   "
SPACE = "    "
REPEAT_MARK = " (повтор)"
CYCLE_MARK = " (цикл)"


def child_mark(child, path, shown):
    """Возвращает пометку для пакета: цикл, повтор или пустую строку."""
    if child in path:
        return CYCLE_MARK
    if child in shown:
        return REPEAT_MARK
    return ""


def add_children(graph, name, prefix, path, shown, lines):
    """Добавляет в дерево зависимости пакета name.

    path — пакеты на пути от корня, shown — уже раскрытые пакеты.
    Повторно встреченный пакет не раскрывается, а помечается.
    """
    children = graph.get(name, [])
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        branch = LAST_BRANCH if is_last else BRANCH
        mark = child_mark(child, path, shown)
        lines.append((prefix + branch, child, mark))
        if mark:
            continue
        shown.add(child)
        next_prefix = prefix + (SPACE if is_last else PIPE)
        add_children(graph, child, next_prefix, path + [child], shown,
                     lines)


def build_tree(graph, root):
    """Строит дерево зависимостей пакета root.

    Возвращает список строк дерева в виде троек:
    (отступ с ветками, имя пакета, пометка).
    """
    lines = [("", root, "")]
    add_children(graph, root, "", [root], {root}, lines)
    return lines
