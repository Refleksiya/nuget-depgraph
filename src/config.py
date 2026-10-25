"""Разбор и проверка параметров командной строки."""

import argparse
import os
import re

from errors import AppError

DEFAULT_REPO = "https://api.nuget.org/v3-flatcontainer"
DEFAULT_DEPTH = "3"
MIN_DEPTH = 1
MAX_DEPTH = 10
PACKAGE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
VERSION_PATTERN = re.compile(r"^[0-9]+(\.[0-9]+)*([.-][A-Za-z0-9.]+)?$")
URL_PREFIXES = ("http://", "https://")
YES = "да"
NO = "нет"
NOT_SET = "не задана"


class Config:
    """Набор проверенных параметров, заданных пользователем."""

    def __init__(self, package, version, repo, test_repo, tree, depth):
        """Сохраняет значения всех параметров приложения."""
        self.package = package
        self.version = version
        self.repo = repo
        self.test_repo = test_repo
        self.tree = tree
        self.depth = depth


def build_parser():
    """Создаёт разборщик опций командной строки."""
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Граф зависимостей пакетов NuGet",
        add_help=True,
    )
    parser.add_argument("--package", default="")
    parser.add_argument("--version", default="")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--test-repo", action="store_true")
    parser.add_argument("--tree", action="store_true")
    parser.add_argument("--max-depth", default=DEFAULT_DEPTH)
    return parser


def check_package(name):
    """Проверяет имя анализируемого пакета."""
    if not name:
        raise AppError("не задано имя пакета, нужен параметр --package")
    if not PACKAGE_PATTERN.match(name):
        raise AppError(f"недопустимое имя пакета: {name}")
    return name


def check_version(value, test_repo):
    """Проверяет версию пакета."""
    if not value:
        if test_repo:
            return ""
        raise AppError("не задана версия пакета, нужен параметр --version")
    if not VERSION_PATTERN.match(value):
        raise AppError(f"недопустимая версия пакета: {value}")
    return value


def check_repo(value, test_repo):
    """Проверяет адрес репозитория или путь к тестовому файлу."""
    if not value:
        raise AppError("не задан репозиторий, нужен параметр --repo")
    if test_repo:
        if not os.path.isfile(value):
            raise AppError(f"файл тестового репозитория не найден: {value}")
        return value
    if not value.startswith(URL_PREFIXES):
        raise AppError(f"адрес репозитория должен начинаться с http: {value}")
    return value


def check_depth(value):
    """Проверяет максимальную глубину анализа зависимостей."""
    try:
        depth = int(value)
    except ValueError:
        raise AppError(f"глубина должна быть целым числом: {value}")
    if depth < MIN_DEPTH or depth > MAX_DEPTH:
        raise AppError(
            f"глубина должна быть от {MIN_DEPTH} до {MAX_DEPTH}: {depth}"
        )
    return depth


def build_config(argv):
    """Разбирает и проверяет все параметры командной строки."""
    args = build_parser().parse_args(argv)
    return Config(
        package=check_package(args.package),
        version=check_version(args.version, args.test_repo),
        repo=check_repo(args.repo, args.test_repo),
        test_repo=args.test_repo,
        tree=args.tree,
        depth=check_depth(args.max_depth),
    )


def flag(value):
    """Переводит логическое значение в слово для вывода."""
    return YES if value else NO


def describe(config):
    """Готовит список строк вида ключ-значение для вывода."""
    return [
        f"package = {config.package}",
        f"version = {config.version or NOT_SET}",
        f"repo = {config.repo}",
        f"test-repo = {flag(config.test_repo)}",
        f"tree = {flag(config.tree)}",
        f"max-depth = {config.depth}",
    ]
