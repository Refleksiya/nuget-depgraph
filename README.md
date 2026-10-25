# Граф зависимостей пакетов NuGet (вариант 20)

## Общее описание

Консольное приложение, которое строит граф зависимостей пакета для
менеджера пакетов .NET (NuGet). Готовые менеджеры пакетов и сторонние
библиотеки для получения зависимостей не используются: данные
забираются напрямую из репозитория, а разбор выполняется самим
приложением.

Выполненные этапы:

1. **Минимальный прототип с конфигурацией** — приложение принимает все
   параметры, проверяет их и выводит на экран в формате ключ-значение.
2. **Сбор данных** — для заданной версии пакета приложение скачивает его
   из официального репозитория NuGet, распаковывает и выводит все
   прямые зависимости.

## Функции и настройки

| Параметр | Описание |
|----------|----------|
| `--package ИМЯ` | Имя анализируемого пакета. Обязательный |
| `--version ВЕРСИЯ` | Версия пакета. Обязательна, кроме тестового режима |
| `--repo АДРЕС` | URL репозитория или путь к файлу тестового репозитория. По умолчанию `https://api.nuget.org/v3-flatcontainer` |
| `--test-repo` | Режим работы с тестовым репозиторием |
| `--tree` | Режим вывода зависимостей в виде ASCII-дерева |
| `--max-depth N` | Максимальная глубина анализа, от 1 до 10, по умолчанию 3 |
| `--help` | Справка по параметрам |

Проверяются все параметры: имя пакета, версия, адрес репозитория,
наличие файла тестового репозитория и диапазон глубины. При ошибке
приложение печатает сообщение и возвращает код 1.

## Как получаются зависимости (этап 2)

Источник данных — официальный API NuGet (`api.nuget.org`), сервис
`v3-flatcontainer`. Всё делается вручную средствами стандартной
библиотеки Python (`urllib`, `zipfile`, `xml.etree`, `json`):

1. Скачивается список опубликованных версий пакета:
   `https://api.nuget.org/v3-flatcontainer/<имя>/index.json`.
   Если пакета нет — ошибка. Если нужной версии нет — ошибка со списком
   последних стабильных версий.
2. Версия приводится к виду, принятому в NuGet: `2.10` → `2.10.0`,
   `4.3.0.0` → `4.3.0`, буквы — в нижний регистр.
3. Скачивается архив пакета:
   `https://api.nuget.org/v3-flatcontainer/<имя>/<версия>/<имя>.<версия>.nupkg`.
   Имя в адресе пишется в нижнем регистре.
4. Архив `.nupkg` — это zip-архив. Он распаковывается в памяти, в его
   корне находится файл описания пакета `<имя>.nuspec`.
5. Файл `.nuspec` (XML) разбирается: из раздела `<dependencies>`
   берутся теги `<dependency id="..." version="..."/>`. Зависимости
   бывают сгруппированы по целевым платформам .NET (`<group
   targetFramework="net6.0">`), поэтому выводятся по группам, а в
   конце — общий список различных зависимостей.

Запись версии зависимости в NuGet: `7.0.2` означает «7.0.2 или новее»,
`[1.0, 2.0)` — «от 1.0 включительно до 2.0 не включительно».

## Структура

```
src/config.py  — разбор и проверка параметров
src/nuget.py   — скачивание пакета и разбор прямых зависимостей
src/main.py    — точка входа и вывод на экран
src/errors.py  — класс ошибки
tests/         — тесты (unittest)
examples/      — файлы описания тестового репозитория
scripts/       — скрипты запуска с разными наборами параметров
```

## Сборка и запуск тестов

Нужен только Python 3.8 и выше, сборка не требуется.

```sh
./run.sh --package Newtonsoft.Json --version 13.0.3   # Linux / macOS
run.bat --package Newtonsoft.Json --version 13.0.3    # Windows
python3 -m unittest discover tests -v                 # тесты
```

## Примеры использования

```
$ ./run.sh --package Serilog --version 3.1.1 --tree --max-depth 5
Параметры запуска:
  package = Serilog
  version = 3.1.1
  repo = https://api.nuget.org/v3-flatcontainer
  test-repo = нет
  tree = да
  max-depth = 5
```

Тестовый репозиторий, пакеты в нём обозначены латинскими буквами:

```
$ ./run.sh --package A --test-repo --repo examples/simple.txt
Параметры запуска:
  package = A
  version = не задана
  repo = examples/simple.txt
  test-repo = да
  tree = нет
  max-depth = 3
```

Обработка ошибок:

```
$ ./run.sh --version 1.0.0
Ошибка: не задано имя пакета, нужен параметр --package

$ ./run.sh --package "bad name" --version 1.0.0
Ошибка: недопустимое имя пакета: bad name

$ ./run.sh --package Serilog --version latest
Ошибка: недопустимая версия пакета: latest

$ ./run.sh --package Serilog --version 1.0.0 --repo nuget.org
Ошибка: адрес репозитория должен начинаться с http: nuget.org

$ ./run.sh --package A --test-repo --repo examples/none.txt
Ошибка: файл тестового репозитория не найден: examples/none.txt

$ ./run.sh --package Serilog --version 1.0.0 --max-depth 99
Ошибка: глубина должна быть от 1 до 10: 99
```

Прямые зависимости пакета (этап 2):

```
$ ./run.sh --package Serilog --version 3.1.1
Параметры запуска:
  ...

Прямые зависимости Serilog 3.1.1:
  [.NETFramework4.6.2]
    System.Diagnostics.DiagnosticSource (версия: 7.0.2)
    System.ValueTuple (версия: 4.5.0)
  [.NETFramework4.7.1]
    System.Diagnostics.DiagnosticSource (версия: 7.0.2)
  [net5.0]
    зависимостей нет
  [net6.0]
    зависимостей нет
  [net7.0]
    зависимостей нет
  [.NETStandard2.0]
    System.Diagnostics.DiagnosticSource (версия: 7.0.2)
  [.NETStandard2.1]
    System.Diagnostics.DiagnosticSource (версия: 7.0.2)

Всего различных прямых зависимостей: 2
  System.Diagnostics.DiagnosticSource
  System.ValueTuple
```

Ошибки при получении данных:

```
$ ./run.sh --package NoSuchPackage.Example --version 1.0.0
Ошибка: пакет не найден в репозитории: NoSuchPackage.Example

$ ./run.sh --package Serilog --version 99.0.0
Ошибка: версия 99.0.0 не найдена, последние версии: ...
```

Готовые скрипты с примерами лежат в папке `scripts/`:
`test_deps_serilog`, `test_deps_newtonsoft`, `test_deps_logging`,
`test_deps_short_version`, `test_err_unknown_package`,
`test_err_unknown_version` (версии `.sh` и `.bat`).
