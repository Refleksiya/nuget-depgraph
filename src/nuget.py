"""Получение прямых зависимостей пакета из репозитория NuGet."""

import io
import json
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as element_tree
import zipfile

from errors import AppError

TIMEOUT_SECONDS = 30
ATTEMPTS = 5
PAUSE_SECONDS = 2
HTTP_NOT_FOUND = 404
NUSPEC_EXTENSION = ".nuspec"
DEPENDENCIES_TAG = "dependencies"
GROUP_TAG = "group"
DEPENDENCY_TAG = "dependency"
FRAMEWORK_ATTR = "targetFramework"
ANY_FRAMEWORK = "любая платформа"
ANY_VERSION = "любая"
MIN_VERSION_PARTS = 3
MAX_VERSION_PARTS = 4
ZERO_PART = "0"
SHOWN_VERSIONS = 5


class Dependency:
    """Одна прямая зависимость: имя пакета и допустимые версии."""

    def __init__(self, name, version):
        """Сохраняет имя пакета-зависимости и диапазон его версий."""
        self.name = name
        self.version = version


def download_once(url):
    """Делает одну попытку скачать данные по адресу."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as answer:
            return answer.read()
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            return None
        raise AppError(f"репозиторий вернул ошибку HTTP {error.code}: {url}")
    except OSError as error:
        raise AppError(f"не удалось подключиться к репозиторию: {error}")


def download(url):
    """Скачивает данные по адресу. Если там ничего нет, возвращает None.

    При сбое сети делается несколько попыток с паузой между ними.
    """
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return download_once(url)
        except AppError:
            if attempt == ATTEMPTS:
                raise
            time.sleep(PAUSE_SECONDS)
    return None


def normalize_version(version):
    """Приводит версию к виду, принятому в NuGet: 1.0 -> 1.0.0."""
    release, dash, suffix = version.partition("-")
    parts = release.split(".")
    while len(parts) < MIN_VERSION_PARTS:
        parts.append(ZERO_PART)
    if len(parts) == MAX_VERSION_PARTS and parts[-1] == ZERO_PART:
        parts.pop()
    return (".".join(parts) + dash + suffix).lower()


def versions_url(repo, package):
    """Строит адрес списка всех опубликованных версий пакета."""
    return f"{repo.rstrip('/')}/{package.lower()}/index.json"


def package_url(repo, package, version):
    """Строит адрес архива .nupkg для заданной версии пакета."""
    name = package.lower()
    return f"{repo.rstrip('/')}/{name}/{version}/{name}.{version}.nupkg"


def fetch_versions(repo, package):
    """Скачивает список опубликованных версий пакета."""
    data = download(versions_url(repo, package))
    if data is None:
        raise AppError(f"пакет не найден в репозитории: {package}")
    try:
        return json.loads(data)["versions"]
    except (ValueError, KeyError):
        raise AppError(f"неверный ответ репозитория для пакета {package}")


def stable_versions(versions):
    """Оставляет только стабильные версии, без предварительных выпусков."""
    return [item for item in versions if "-" not in item]


def find_version(versions, version):
    """Проверяет, что нужная версия опубликована, и возвращает её."""
    wanted = normalize_version(version)
    if wanted not in versions:
        shown = stable_versions(versions) or versions
        latest = ", ".join(shown[-SHOWN_VERSIONS:])
        raise AppError(
            f"версия {version} не найдена, последние версии: {latest}"
        )
    return wanted


def read_nuspec(archive_data):
    """Распаковывает архив .nupkg и возвращает содержимое файла .nuspec."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_data))
    except zipfile.BadZipFile:
        raise AppError("файл пакета повреждён: это не zip-архив")
    with archive:
        for name in archive.namelist():
            if name.endswith(NUSPEC_EXTENSION) and "/" not in name:
                return archive.read(name)
    raise AppError("в пакете нет файла описания .nuspec")


def local_name(element):
    """Возвращает имя тега XML без пространства имён."""
    return element.tag.split("}")[-1]


def make_dependency(element):
    """Создаёт зависимость из тега dependency."""
    name = element.get("id")
    if not name:
        raise AppError("в файле .nuspec у зависимости нет имени")
    return Dependency(name, element.get("version", ANY_VERSION))


def read_group(group):
    """Читает все зависимости из одной группы для платформы."""
    result = []
    for child in group:
        if local_name(child) == DEPENDENCY_TAG:
            result.append(make_dependency(child))
    return result


def read_dependencies_block(block):
    """Читает раздел dependencies с группами по платформам или без них."""
    groups = {}
    for child in block:
        tag = local_name(child)
        if tag == GROUP_TAG:
            framework = child.get(FRAMEWORK_ATTR, ANY_FRAMEWORK)
            groups[framework] = read_group(child)
        elif tag == DEPENDENCY_TAG:
            groups.setdefault(ANY_FRAMEWORK, [])
            groups[ANY_FRAMEWORK].append(make_dependency(child))
    return groups


def parse_dependencies(nuspec):
    """Разбирает .nuspec и возвращает зависимости по платформам."""
    try:
        root = element_tree.fromstring(nuspec)
    except element_tree.ParseError:
        raise AppError("не удалось разобрать файл .nuspec")
    for element in root.iter():
        if local_name(element) == DEPENDENCIES_TAG:
            return read_dependencies_block(element)
    return {}


def merge_groups(groups):
    """Объединяет зависимости всех платформ в один список без повторов."""
    merged = []
    names = []
    for dependencies in groups.values():
        for dependency in dependencies:
            if dependency.name not in names:
                names.append(dependency.name)
                merged.append(dependency)
    return merged


def unique_dependencies(groups):
    """Собирает имена зависимостей из всех групп без повторов."""
    return [dependency.name for dependency in merge_groups(groups)]


def download_dependencies(repo, package, version):
    """Скачивает архив пакета точной версии и разбирает его зависимости."""
    archive_data = download(package_url(repo, package, version))
    if archive_data is None:
        raise AppError(f"архив пакета {package} {version} не найден")
    return parse_dependencies(read_nuspec(archive_data))


def get_direct_dependencies(repo, package, version):
    """Скачивает пакет заданной версии и возвращает его зависимости."""
    found = find_version(fetch_versions(repo, package), version)
    return download_dependencies(repo, package, found)


def version_key(version):
    """Превращает версию в кортеж чисел, чтобы версии можно было сравнить."""
    release = version.partition("-")[0]
    return tuple(int(part) for part in release.split(".") if part.isdigit())


def lower_bound(version_range):
    """Возвращает нижнюю границу диапазона версий и признак её включения."""
    text = version_range.strip()
    if text == ANY_VERSION:
        return "", True
    inclusive = not text.startswith("(")
    lower = text.strip("[]()").split(",")[0].strip()
    return lower, inclusive


def fits_lower_bound(version, lower, inclusive):
    """Проверяет, что версия не ниже нижней границы диапазона."""
    if not lower:
        return True
    if inclusive:
        return version_key(version) >= version_key(lower)
    return version_key(version) > version_key(lower)


def choose_version(versions, version_range):
    """Выбирает наименьшую подходящую версию, как это делает NuGet."""
    lower, inclusive = lower_bound(version_range)
    candidates = stable_versions(versions) or versions
    for version in sorted(candidates, key=version_key):
        if fits_lower_bound(version, lower, inclusive):
            return version
    raise AppError(f"нет версии, подходящей под диапазон {version_range}")
