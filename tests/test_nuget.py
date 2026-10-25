"""Тесты получения прямых зависимостей из репозитория NuGet."""

import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import nuget
from errors import AppError

REPO = "https://api.nuget.org/v3-flatcontainer"

GROUPED_NUSPEC = b"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>Demo</id>
    <version>1.0.0</version>
    <dependencies>
      <group targetFramework="net462">
        <dependency id="First" version="[1.0.0, )" />
        <dependency id="Second" version="2.0.0" />
      </group>
      <group targetFramework="net8.0">
        <dependency id="First" version="[1.0.0, )" />
      </group>
      <group targetFramework="netstandard2.0" />
    </dependencies>
  </metadata>
</package>
"""

FLAT_NUSPEC = b"""<?xml version="1.0"?>
<package>
  <metadata>
    <id>Old</id>
    <dependencies>
      <dependency id="Alpha" version="1.0" />
      <dependency id="Beta" />
    </dependencies>
  </metadata>
</package>
"""

EMPTY_NUSPEC = b"""<?xml version="1.0"?>
<package><metadata><id>Lonely</id></metadata></package>
"""


def make_archive(files):
    """Собирает zip-архив в памяти из словаря имя -> содержимое."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


class TestVersions(unittest.TestCase):
    """Тесты приведения версий и построения адресов."""

    def test_short_version(self):
        """Короткая версия дополняется нулями."""
        self.assertEqual(nuget.normalize_version("1.0"), "1.0.0")

    def test_fourth_zero_removed(self):
        """Нулевая четвёртая часть версии отбрасывается."""
        self.assertEqual(nuget.normalize_version("4.3.0.0"), "4.3.0")

    def test_prerelease_lowercase(self):
        """Предварительная версия переводится в нижний регистр."""
        self.assertEqual(nuget.normalize_version("2.0.0-Beta1"),
                         "2.0.0-beta1")

    def test_package_url(self):
        """Адрес архива строится из имени в нижнем регистре."""
        self.assertEqual(
            nuget.package_url(REPO + "/", "Serilog", "3.1.1"),
            REPO + "/serilog/3.1.1/serilog.3.1.1.nupkg",
        )

    def test_versions_url(self):
        """Адрес списка версий строится из имени в нижнем регистре."""
        self.assertEqual(nuget.versions_url(REPO, "Serilog"),
                         REPO + "/serilog/index.json")

    def test_find_version(self):
        """Опубликованная версия находится после приведения."""
        self.assertEqual(nuget.find_version(["1.0.0", "2.0.0"], "2.0"),
                         "2.0.0")

    def test_stable_versions(self):
        """Предварительные выпуски не попадают в список стабильных."""
        self.assertEqual(nuget.stable_versions(["1.0.0", "2.0.0-dev"]),
                         ["1.0.0"])

    def test_missing_version(self):
        """Неопубликованная версия вызывает ошибку."""
        with self.assertRaises(AppError):
            nuget.find_version(["1.0.0"], "9.9.9")


class TestNuspec(unittest.TestCase):
    """Тесты распаковки архива и разбора файла .nuspec."""

    def test_grouped(self):
        """Зависимости читаются по группам платформ."""
        groups = nuget.parse_dependencies(GROUPED_NUSPEC)
        self.assertEqual(list(groups),
                         ["net462", "net8.0", "netstandard2.0"])
        names = [item.name for item in groups["net462"]]
        self.assertEqual(names, ["First", "Second"])
        self.assertEqual(groups["netstandard2.0"], [])

    def test_flat(self):
        """Зависимости без групп относятся к любой платформе."""
        groups = nuget.parse_dependencies(FLAT_NUSPEC)
        items = groups[nuget.ANY_FRAMEWORK]
        self.assertEqual([item.name for item in items], ["Alpha", "Beta"])
        self.assertEqual(items[1].version, nuget.ANY_VERSION)

    def test_no_dependencies(self):
        """Пакет без раздела dependencies не имеет зависимостей."""
        self.assertEqual(nuget.parse_dependencies(EMPTY_NUSPEC), {})

    def test_broken_xml(self):
        """Повреждённый XML вызывает ошибку."""
        with self.assertRaises(AppError):
            nuget.parse_dependencies(b"<package>")

    def test_unique(self):
        """Общий список зависимостей не содержит повторов."""
        groups = nuget.parse_dependencies(GROUPED_NUSPEC)
        self.assertEqual(nuget.unique_dependencies(groups),
                         ["First", "Second"])

    def test_read_nuspec(self):
        """Файл .nuspec находится в корне архива."""
        archive = make_archive({"_rels/.rels": "x",
                                "Demo.nuspec": GROUPED_NUSPEC})
        self.assertEqual(nuget.read_nuspec(archive), GROUPED_NUSPEC)

    def test_archive_without_nuspec(self):
        """Архив без .nuspec вызывает ошибку."""
        with self.assertRaises(AppError):
            nuget.read_nuspec(make_archive({"lib/a.dll": "x"}))

    def test_not_archive(self):
        """Данные, которые не являются zip-архивом, вызывают ошибку."""
        with self.assertRaises(AppError):
            nuget.read_nuspec(b"not a zip")


class TestDownload(unittest.TestCase):
    """Тесты получения пакета с подменой сетевых запросов."""

    def test_direct_dependencies(self):
        """Пакет скачивается, распаковывается и разбирается."""
        index = json.dumps({"versions": ["1.0.0"]}).encode()
        archive = make_archive({"Demo.nuspec": GROUPED_NUSPEC})
        with mock.patch.object(nuget, "download",
                               side_effect=[index, archive]) as fake:
            groups = nuget.get_direct_dependencies(REPO, "Demo", "1.0")
        self.assertIn("net8.0", groups)
        fake.assert_called_with(REPO + "/demo/1.0.0/demo.1.0.0.nupkg")

    def test_unknown_package(self):
        """Отсутствующий в репозитории пакет вызывает ошибку."""
        with mock.patch.object(nuget, "download", return_value=None):
            with self.assertRaises(AppError):
                nuget.get_direct_dependencies(REPO, "NoSuch", "1.0.0")

    def test_bad_index(self):
        """Неверный ответ со списком версий вызывает ошибку."""
        with mock.patch.object(nuget, "download", return_value=b"{}"):
            with self.assertRaises(AppError):
                nuget.fetch_versions(REPO, "Demo")

    def test_no_connection(self):
        """Ошибка сети превращается в понятное сообщение."""
        with mock.patch("urllib.request.urlopen",
                        side_effect=OSError("нет сети")):
            with self.assertRaises(AppError):
                nuget.download(REPO)


if __name__ == "__main__":
    unittest.main()
