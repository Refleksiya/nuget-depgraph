"""Источник зависимостей: официальный репозиторий NuGet."""

from nuget import (
    choose_version,
    download_dependencies,
    fetch_versions,
    find_version,
    merge_groups,
)


class NugetSource:
    """Получает зависимости пакетов из репозитория NuGet по его URL."""

    def __init__(self, repo, package, version):
        """Запоминает репозиторий и проверяет версию корневого пакета."""
        self.repo = repo
        self.published_versions = {}
        self.groups = {}
        found = find_version(self.published(package), version)
        self.versions = {package: found}

    def published(self, name):
        """Возвращает опубликованные версии пакета, скачивая список один раз."""
        if name not in self.published_versions:
            self.published_versions[name] = fetch_versions(self.repo, name)
        return self.published_versions[name]

    def remember_version(self, dependency):
        """Выбирает версию зависимости, если она ещё не была выбрана."""
        if dependency.name not in self.versions:
            versions = self.published(dependency.name)
            found = choose_version(versions, dependency.version)
            self.versions[dependency.name] = found

    def dependencies(self, name):
        """Скачивает пакет и возвращает имена его прямых зависимостей."""
        groups = download_dependencies(self.repo, name, self.versions[name])
        self.groups[name] = groups
        names = []
        for dependency in merge_groups(groups):
            self.remember_version(dependency)
            names.append(dependency.name)
        return names

    def label(self, name):
        """Возвращает подпись пакета: имя и выбранную версию."""
        return f"{name} {self.versions[name]}"
