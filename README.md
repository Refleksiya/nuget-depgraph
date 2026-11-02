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
3. **Основные операции** — строится полный граф зависимостей с учётом
   транзитивности (обход в ширину с рекурсией), учитывается максимальная
   глубина, находятся циклические зависимости. Поддержан режим
   тестового репозитория.

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

## Построение графа (этап 3)

**Алгоритм — обход в ширину (BFS) с рекурсией** (`src/graph.py`):

1. Первый уровень — сам анализируемый пакет.
2. Функция `visit_level` берёт все пакеты текущего уровня, загружает
   их прямые зависимости и собирает из ещё не встречавшихся пакетов
   следующий уровень.
3. Затем `visit_level` вызывает сама себя для следующего уровня — это
   и есть рекурсия. Обход идёт по уровням: сначала ближние пакеты,
   потом дальние.
4. Рекурсия останавливается, когда следующий уровень пуст или
   достигнута максимальная глубина `--max-depth`. Глубина — число шагов
   от анализируемого пакета: при `--max-depth 1` загружаются только
   прямые зависимости.

Результат — словарь «пакет → список его прямых зависимостей».

**Циклические зависимости.** Каждый пакет загружается один раз: если
пакет уже есть в графе, повторно он не обходится, поэтому цикл не
приводит к бесконечной работе. После построения граф обходится в
глубину (`find_cycles`), и найденные циклы выводятся в виде
`A -> B -> C -> A`.

**Выбор версий зависимостей.** В `.nuspec` у зависимости указан
диапазон версий. Как и NuGet, приложение выбирает наименьшую
опубликованную стабильную версию, которая не ниже нижней границы
диапазона: для `[1.0.0, )` и `1.0.0` — это `1.0.0`, если она
опубликована. Зависимости всех целевых платформ объединяются.

**Режим тестового репозитория** (`--test-repo`). Вместо URL задаётся
путь к текстовому файлу с описанием графа. Пакеты называются большими
латинскими буквами, каждая строка — пакет и его прямые зависимости:

```
A: B C
B: D
C: D
D:
```

Проверяется, что имена состоят из больших латинских букв, в строке есть
двоеточие, пакет не описан дважды и анализируемый пакет есть в файле.
Пакет, который не описан отдельной строкой, считается пакетом без
зависимостей.

Примеры файлов в папке `examples/`:

| Файл | Что показывает |
|------|----------------|
| `simple.txt` | граф без циклов, D — общая зависимость B и C |
| `cycle.txt` | цикл A → B → C → A |
| `complex.txt` | два цикла: C → G → C и A → D → H → A |
| `chain.txt` | длинная цепочка для проверки максимальной глубины |
| `bad_name.txt` | ошибка: имя пакета из маленьких букв |

## Структура

```
src/config.py        — разбор и проверка параметров
src/nuget.py         — скачивание пакета, разбор зависимостей, выбор версий
src/nuget_source.py  — зависимости из репозитория NuGet для построения графа
src/file_source.py   — зависимости из файла тестового репозитория
src/graph.py         — построение графа (BFS с рекурсией) и поиск циклов
src/output.py        — вывод результатов на экран
src/main.py          — точка входа
src/errors.py        — класс ошибки
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

Граф зависимостей в тестовом режиме (этап 3):

```
$ ./run.sh --package A --test-repo --repo examples/simple.txt
...
Граф зависимостей (BFS, максимальная глубина 3):
  A -> B, C
  B -> D
  C -> D
  D -> нет зависимостей
Всего пакетов в графе: 4
Циклические зависимости: не найдены
```

Граф с двумя циклами:

```
$ ./run.sh --package A --test-repo --repo examples/complex.txt --max-depth 5
...
Граф зависимостей (BFS, максимальная глубина 5):
  A -> B, C, D
  B -> E, F
  C -> F, G
  D -> H
  E -> нет зависимостей
  F -> I
  G -> C
  H -> A
  I -> нет зависимостей
Всего пакетов в графе: 9
Циклические зависимости:
  C -> G -> C
  A -> D -> H -> A
```

Ограничение глубины:

```
$ ./run.sh --package A --test-repo --repo examples/chain.txt --max-depth 2
...
Граф зависимостей (BFS, максимальная глубина 2):
  A -> B
  B -> C
Всего пакетов в графе: 3
Зависимости не загружались (достигнута максимальная глубина):
  C
Циклические зависимости: не найдены
```

Ошибка в файле тестового репозитория:

```
$ ./run.sh --package A --test-repo --repo examples/bad_name.txt
...
Ошибка: строка 1: имя пакета должно состоять из больших латинских букв: c
```

Граф реального пакета из NuGet (прямые зависимости по платформам
пропущены):

```
$ ./run.sh --package Microsoft.Extensions.Logging --version 8.0.0 --max-depth 2
...
Граф зависимостей (BFS, максимальная глубина 2):
  Microsoft.Extensions.Logging 8.0.0 ->
      Microsoft.Bcl.AsyncInterfaces 8.0.0,
      Microsoft.Extensions.DependencyInjection 8.0.0,
      Microsoft.Extensions.Logging.Abstractions 8.0.0,
      Microsoft.Extensions.Options 8.0.0,
      System.Diagnostics.DiagnosticSource 8.0.0, System.ValueTuple 4.5.0
  Microsoft.Bcl.AsyncInterfaces 8.0.0 ->
      System.Threading.Tasks.Extensions 4.5.4
  Microsoft.Extensions.DependencyInjection 8.0.0 ->
      Microsoft.Bcl.AsyncInterfaces 8.0.0,
      Microsoft.Extensions.DependencyInjection.Abstractions 8.0.0,
      System.Threading.Tasks.Extensions 4.5.4
  Microsoft.Extensions.Logging.Abstractions 8.0.0 ->
      Microsoft.Extensions.DependencyInjection.Abstractions 8.0.0,
      System.Buffers 4.5.1, System.Memory 4.5.5
  Microsoft.Extensions.Options 8.0.0 ->
      Microsoft.Extensions.DependencyInjection.Abstractions 8.0.0,
      Microsoft.Extensions.Primitives 8.0.0, System.ValueTuple 4.5.0,
      System.ComponentModel.Annotations 5.0.0
  System.Diagnostics.DiagnosticSource 8.0.0 ->
      System.Memory 4.5.5, System.Runtime.CompilerServices.Unsafe 6.0.0
  System.ValueTuple 4.5.0 -> NETStandard.Library 1.6.1
Всего пакетов в графе: 15
Зависимости не загружались (достигнута максимальная глубина):
      System.Threading.Tasks.Extensions 4.5.4,
      Microsoft.Extensions.DependencyInjection.Abstractions 8.0.0,
      System.Buffers 4.5.1, System.Memory 4.5.5,
      Microsoft.Extensions.Primitives 8.0.0,
      System.ComponentModel.Annotations 5.0.0,
      System.Runtime.CompilerServices.Unsafe 6.0.0, NETStandard.Library 1.6.1
Циклические зависимости: не найдены
```

Скрипты этапа 3: `test_graph_simple`, `test_graph_cycle`,
`test_graph_complex`, `test_graph_depth`, `test_graph_serilog`,
`test_graph_logging`, `test_err_bad_test_file`,
`test_err_unknown_test_package`.
