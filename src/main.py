"""Точка входа инструмента визуализации графа зависимостей."""

import sys

from config import build_config, describe
from errors import AppError

EXIT_OK = 0
EXIT_ERROR = 1


def run(argv):
    """Выполняет работу приложения и возвращает код возврата."""
    try:
        config = build_config(argv)
    except AppError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print("Параметры запуска:")
    for line in describe(config):
        print(f"  {line}")
    return EXIT_OK


def main():
    """Запускает приложение с аргументами командной строки."""
    return run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
