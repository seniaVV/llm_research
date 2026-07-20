# Агрометрикс: подробный README для передачи данных ИИ-разработчику

Дата версии: 2026-07-02  
Пакет: `agrometrics_ai_full_handoff_3_fields_20260701`  
Назначение: локальная выгрузка данных по трем полям для разработки ИИ-интеграции

## 1. Коротко: что это такое

Это переносимый набор данных из локальной системы «Агрометрикс». Он нужен, чтобы другой разработчик мог у себя на компьютере поднять такой же фрагмент данных и спокойно делать ИИ-интеграцию без доступа к твоему ноутбуку, твоему Docker volume и внешним API.

В пакете лежат:

- реальные границы трех полей;
- записи PostgreSQL/PostGIS, которые описывают поля, сцены, растровые assets, погоду, почвы и jobs;
- реальные файлы из локального S3/MinIO: GeoTIFF, маски, индексные слои Sentinel-2 и радарные слои Sentinel-1;
- готовые JSON/JSONL/CSV файлы для быстрого анализа без подключения к базе;
- скрипты импорта и проверки.

Если совсем просто: `PostgreSQL` отвечает на вопрос «что это за данные и как они связаны», а `MinIO/S3` хранит тяжелые файлы снимков и индексов. ИИ-разработчику обычно нужны оба слоя.

## 2. Какие поля входят в выгрузку

Выгрузка намеренно ограничена тремя кадастровыми участками:

```text
23:27:1101000:1039
23:27:1101000:1040
23:27:1101000:1041
```

Это важно: пакет не является дампом всей системы. Он содержит только данные, связанные с этими тремя полями, чтобы разработчик не получил лишнее и не запутался.

## 3. Что нужно понимать про архитектуру

Упрощенно система устроена так:

```mermaid
flowchart TD
    A["Frontend / web map"] --> B["API Gateway"]
    B --> C["field-service"]
    B --> D["tile-api"]
    C --> E["PostgreSQL + PostGIS"]
    D --> E
    D --> F["MinIO / S3"]
    G["Sentinel collector / workers"] --> E
    G --> F
    H["AI integration"] --> E
    H --> F
    H --> I["metadata JSON/JSONL files"]
```

Главная идея:

- `PostgreSQL + PostGIS` хранит структурированные данные: поля, геометрию, сцены, ссылки на растры, погоду, почвы.
- `MinIO / S3` хранит тяжелые файлы: `.tif`, `.tiff`, `manifest.json`.
- `raster_service.assets` в Postgres связывает запись в базе с конкретным файлом в S3 через пару `bucket + object_key`.
- `metadata/*.jsonl` в этом пакете — удобная плоская копия важной части базы, чтобы ИИ-разработчик мог начать без SQL.

## 4. Структура пакета

Корень пакета:

```text
agrometrics_ai_full_handoff_3_fields_20260701/
  README.md
  README_FOR_AI_INTEGRATION.md
  manifest_full.json
  db/
    bootstrap_schema.sql
    seed_3_fields.sql
  metadata/
    assets/
    docs/
    fields/
    sampled_statistics/
    soil/
    vra/
    weather/
  s3/
    _object_inventory.json
    _object_manifest.jsonl
    agrometrics-raw/
  scripts/
    import_local.sh
    verify_local.sh
```

Что здесь главное:

- `README.md` — короткая инструкция.
- `README_FOR_AI_INTEGRATION.md` — этот подробный документ.
- `manifest_full.json` — машинно-читаемая сводка всего пакета.
- `db/seed_3_fields.sql` — self-contained SQL-скрипт, который создает недостающую схему и восстанавливает данные в Postgres.
- `db/bootstrap_schema.sql` — тот же минимальный bootstrap схемы отдельным файлом; обычно нужен только для ручной отладки.
- `metadata/assets/assets_catalog.jsonl` — главный каталог всех растровых данных.
- `s3/agrometrics-raw/...` — реальные файлы снимков и индексов.
- `scripts/import_local.sh` — автоматический импорт в локальный Docker.
- `scripts/verify_local.sh` — проверка, что импорт прошел корректно.

## 5. Что именно входит по количествам

В базе:

| Сущность | Количество | Зачем нужна |
|---|---:|---|
| Поля | 3 | Геометрия, культура, площадь, карточные показатели |
| Scenes | 776 | Даты и источники спутниковых сцен |
| Assets | 17 082 | Ссылки на конкретные raster-файлы в S3 |
| Soil profiles | 3 | Почвенные профили SoilGrids/локального кеша |
| SoilGrids point cache | 1 | Локальный кеш ответа SoilGrids |
| Weather snapshots | 34 | Кеш погоды по полям |
| Jobs | 32 | История загрузок/обработок |

В S3/MinIO:

| Тип | Количество |
|---|---:|
| Всего объектов | 17 082 |
| Общий размер | 2.86 GiB |
| Ошибки выгрузки | 0 |

По сенсорам:

| Сенсор | Количество assets / S3 objects |
|---|---:|
| Sentinel-2 L2A | 12 832 |
| Sentinel-1 GRD | 4 224 |
| Служебные manifest-записи без sensor | 26 |

## 6. Минимальные требования для разработчика

Разработчику нужен:

- локальный проект «Агрометрикс» с `docker-compose.yml`;
- Docker Desktop или аналог;
- распакованная папка `agrometrics_ai_full_handoff_3_fields_20260701`;
- желательно `python3`, чтобы читать JSONL и делать быстрые проверки;
- если он будет читать GeoTIFF вне приложения, нужны GIS-библиотеки, например `rasterio`, `rio-cogeo`, `gdal`, `numpy`.

Для простого импорта в систему GIS-библиотеки не нужны: скрипт использует Docker-сервисы проекта.

## 7. Локальные dev-доступы

В стандартном `.env.example` проекта используются dev-учетки:

PostgreSQL:

```text
host: 127.0.0.1
port: 5432
database: agrometrics
user: agrometrics
password: agrometrics_dev_password
```

Строка подключения с компьютера:

```text
postgres://agrometrics:agrometrics_dev_password@127.0.0.1:5432/agrometrics?sslmode=disable
```

Внутри Docker:

```text
postgres://agrometrics:agrometrics_dev_password@postgres:5432/agrometrics?sslmode=disable
```

MinIO / S3:

```text
S3 endpoint from host: http://127.0.0.1:9100
MinIO console: http://127.0.0.1:9101
access key: agrometrics
secret key: agrometrics_dev_password
bucket: agrometrics-raw
```

RabbitMQ, если понадобится:

```text
UI: http://127.0.0.1:15672
user: agrometrics
password: agrometrics_dev_password
```

Keycloak admin, если понадобится:

```text
UI: http://127.0.0.1:8180
user: admin
password: admin_dev_password
```

Для текущей задачи ИИ-интеграции чаще всего нужны только PostgreSQL, MinIO и файлы из `metadata`.

## 8. Как импортировать пакет в локальный проект

### Вариант A: пакет лежит внутри проекта

Из корня проекта:

```bash
./exports/agrometrics_ai_full_handoff_3_fields_20260701/scripts/import_local.sh
```

### Вариант B: пакет лежит где-то отдельно

Из любого места:

```bash
/path/to/agrometrics_ai_full_handoff_3_fields_20260701/scripts/import_local.sh /path/to/Веб-ГИС
```

### Если используется `.env`, а не `.env.example`

```bash
ENV_FILE=.env /path/to/agrometrics_ai_full_handoff_3_fields_20260701/scripts/import_local.sh /path/to/Веб-ГИС
```

Что делает `import_local.sh`:

1. Заходит в проект.
2. Поднимает `postgres`, `minio`, `minio-init`.
3. Выполняет `db/seed_3_fields.sql` в Postgres.
4. Загружает содержимое `s3/agrometrics-raw` в MinIO bucket `agrometrics-raw`.

Скрипт можно запускать повторно. SQL seed сделан idempotent: он удаляет и заново вставляет только этот переносимый subset по трем полям.

## 9. Как проверить импорт

После импорта:

```bash
/path/to/agrometrics_ai_full_handoff_3_fields_20260701/scripts/verify_local.sh /path/to/Веб-ГИС
```

Ожидаемые counts:

```text
fields             3
soil_profiles      3
weather_snapshots  34
assets             17082
scenes             776
```

Также скрипт проверяет, что в MinIO доступен конкретный объект из S3 manifest.

## 10. Где искать данные для ИИ

ИИ-разработчику лучше начинать с этих файлов:

```text
metadata/assets/assets_catalog.jsonl
metadata/sampled_statistics/core_index_statistics_sampled.jsonl
metadata/fields/fields.geojson
metadata/soil/soil_profiles.json
metadata/weather/weather_latest_by_field.json
metadata/vra/vra_summaries.json
metadata/vra/vra_grid_*.json
```

Роль каждого файла:

| Файл | Зачем нужен |
|---|---|
| `fields.geojson` | Границы полей и базовые свойства |
| `assets_catalog.jsonl` | Полный каталог всех raster assets |
| `core_index_statistics_sampled.jsonl` | Быстрая выборка статистик по индексам |
| `soil_profiles.json` | Почвенный контекст |
| `weather_latest_by_field.json` | Последняя погодная сводка |
| `vra_grid_*.json` | Сетка карты-задания / зоны дифференцированного внесения |
| `vra_summaries.json` | Краткая сводка VRA по полям |

## 11. Как связаны Postgres и S3

В Postgres есть таблица:

```text
raster_service.assets
```

В ней каждая строка описывает один файл:

```text
assetId
fieldId
sensor
capturedOn
group
indexKey
bucket
objectKey
```

В S3 файл лежит по правилу:

```text
s3/{bucket}/{objectKey}
```

Например, если в `assets_catalog.jsonl` есть:

```json
{
  "bucket": "agrometrics-raw",
  "objectKey": "sentinel/.../output/Sentinel-2-L2A/2026-06-16/raw_indexes/NDVI.tif"
}
```

То локальный файл в пакете будет здесь:

```text
s3/agrometrics-raw/sentinel/.../output/Sentinel-2-L2A/2026-06-16/raw_indexes/NDVI.tif
```

Это главный принцип навигации по выгрузке.

## 12. Что такое JSONL и почему он здесь используется

`JSONL` означает JSON Lines: одна строка — один JSON-объект.

Пример:

```jsonl
{"fieldId":"23:27:1101000:1040","sensor":"Sentinel-2-L2A","indexKey":"NDVI"}
{"fieldId":"23:27:1101000:1040","sensor":"Sentinel-1-GRD","indexKey":"RVI"}
```

Почему это удобно:

- файл можно читать построчно, не загружая целиком в память;
- хорошо подходит для пайплайнов ИИ и feature engineering;
- легко фильтровать по `fieldId`, `sensor`, `capturedOn`, `indexKey`.

Пример чтения на Python:

```python
import json
from pathlib import Path

bundle = Path("agrometrics_ai_full_handoff_3_fields_20260701")
catalog_path = bundle / "metadata" / "assets" / "assets_catalog.jsonl"

with catalog_path.open() as f:
    for line in f:
        row = json.loads(line)
        if row.get("fieldId") == "23:27:1101000:1040" and row.get("indexKey") == "NDVI":
            print(row["capturedOn"], row["bucket"], row["objectKey"])
```

## 13. Как найти конкретный raster-файл

Пример: найти Sentinel-2 NDVI для поля `23:27:1101000:1040`.

```python
import json
from pathlib import Path

bundle = Path("agrometrics_ai_full_handoff_3_fields_20260701")
catalog_path = bundle / "metadata/assets/assets_catalog.jsonl"

matches = []
for line in catalog_path.read_text().splitlines():
    row = json.loads(line)
    if (
        row.get("fieldId") == "23:27:1101000:1040"
        and row.get("sensor") == "Sentinel-2-L2A"
        and row.get("group") == "raw_indexes"
        and row.get("indexKey") == "NDVI"
    ):
        local_path = bundle / "s3" / row["bucket"] / row["objectKey"]
        matches.append((row["capturedOn"], local_path))

for date, path in sorted(matches)[-5:]:
    print(date, path)
```

Пример: найти Sentinel-1 RVI для того же поля.

```python
import json
from pathlib import Path

bundle = Path("agrometrics_ai_full_handoff_3_fields_20260701")
catalog_path = bundle / "metadata/assets/assets_catalog.jsonl"

for line in catalog_path.read_text().splitlines():
    row = json.loads(line)
    if (
        row.get("fieldId") == "23:27:1101000:1040"
        and row.get("sensor") == "Sentinel-1-GRD"
        and row.get("group") == "raw_indexes"
        and row.get("indexKey") == "RVI"
    ):
        print(row["capturedOn"], bundle / "s3" / row["bucket"] / row["objectKey"])
```

## 14. Sentinel-2: что это и как его использовать

Sentinel-2 L2A — оптический спутник. Он видит отраженный солнечный свет в разных спектральных каналах.

Для агрономии Sentinel-2 полезен для:

- оценки зеленой биомассы;
- контроля неоднородности поля;
- поиска стрессов;
- динамики сезона;
- построения NDVI/NDMI/NDRE/NDWI и других индексов.

Важная особенность: Sentinel-2 зависит от облаков, теней и снега. Поэтому для S2 в пакете есть маски:

```text
mask_clouds
mask_cloud_shadows
mask_water
mask_snow_ice
SCL_classes
SCL_RGBA
```

Если ИИ анализирует S2-индексы, нельзя слепо верить всем пикселям. Облака и тени надо исключать или помечать как `no_data`.

Основные S2-индексы:

| Индекс | Что примерно показывает |
|---|---|
| `NDVI` | Зеленая биомасса / активность растительности |
| `NDMI` | Влажность растительности / водный стресс |
| `NDWI` | Вода / переувлажнение / водные поверхности |
| `NDRE` | Хлорофилл, особенно полезен на более развитой культуре |
| `EVI` | Альтернатива NDVI, менее чувствительна к насыщению |
| `SAVI` | Индекс с поправкой на почвенный фон |
| `BSI` | Открытая почва / bare soil |
| `NBR` | Повреждения, стресс, иногда полезен для деградации |
| `CIg` | Chlorophyll Index Green |
| `PSRI` | Старение/стресс листового аппарата |

## 15. Sentinel-1: что это и почему он важен

Sentinel-1 GRD — радарный спутник. Он работает в микроволновом диапазоне и не зависит от солнечного света.

Главное отличие от Sentinel-2:

- Sentinel-1 видит сквозь облака;
- облачная маска к Sentinel-1 не применяется;
- значения сложнее интерпретировать напрямую;
- данные полезны для структуры поверхности, влажности, последствий затопления, грубой оценки состояния растительного покрова.

В пакете Sentinel-1 есть явно:

```text
s3/agrometrics-raw/sentinel/.../output/Sentinel-1-GRD/...
```

Количество:

```text
Sentinel-1-GRD: 4 224 объектов
```

Основные S1-слои:

| Слой | Смысл |
|---|---|
| `VV_dB` | Обратное рассеяние в VV-поляризации |
| `VH_dB` | Обратное рассеяние в VH-поляризации |
| `RVI` | Radar Vegetation Index |
| `NDpol` | Нормализованный поляризационный индекс |
| `CR_lin_VH_over_VV` | Отношение VH/VV в линейной шкале |

Пример конкретного файла Sentinel-1:

```text
s3/agrometrics-raw/sentinel/11111111-1111-1111-1111-111111111111/6953d806-500d-4945-9567-8e0c2a3b027f/output/Sentinel-1-GRD/2026-01-01/raw_indexes/RVI.tif
```

Когда использовать S1 в ИИ:

- если S2 закрыт облаками;
- если нужно учитывать последствия переувлажнения/затопления;
- если нужно сравнить структурное состояние поверхности с оптическими индексами;
- если модель должна быть устойчивой к пропускам оптических данных.

Чего не делать:

- не применять облачную маску к S1;
- не смешивать S1 и S2 значения как будто они в одной физической шкале;
- не объяснять фермеру `VV_dB` без агрономического перевода.

## 16. Что такое `raw`, `raw_indexes`, `color_indexes`

В каталогах снимков часто встречаются группы:

```text
raw
raw_indexes
color_indexes
test_download.tiff
```

Их смысл:

| group | Для чего |
|---|---|
| `raw` | Исходные/объединенные raster-данные, например `merged_image.tiff`, `part_0_0.tiff` |
| `raw_indexes` | Численные индексы, которые лучше использовать для анализа и ML |
| `color_indexes` | Визуализированные TIFF для карты, удобны человеку, хуже для расчетов |
| `test_download.tiff` | Служебный тестовый файл загрузки |

Для ИИ почти всегда начинать нужно с `raw_indexes`, потому что там численные значения индексов, а не раскрашенная картинка.

## 17. Как читать GeoTIFF

Если у разработчика установлен `rasterio`, можно быстро посмотреть форму растра и статистику:

```python
from pathlib import Path
import rasterio
import numpy as np

path = Path("agrometrics_ai_full_handoff_3_fields_20260701/s3/agrometrics-raw/sentinel/.../raw_indexes/NDVI.tif")

with rasterio.open(path) as src:
    band = src.read(1).astype("float32")
    nodata = src.nodata
    mask = np.isfinite(band)
    if nodata is not None:
        mask &= band != nodata
    values = band[mask]
    print(src.crs, src.width, src.height)
    print(float(values.min()), float(values.mean()), float(values.max()))
```

Если путь длинный, лучше получить его из `assets_catalog.jsonl`, как показано выше.

## 18. Важные таблицы Postgres

### `field_service.fields`

Главная таблица полей.

Важные поля:

| Колонка | Смысл |
|---|---|
| `id` | UUID поля внутри системы |
| `external_id` | кадастровый номер / внешний ID |
| `crop_key` | культура |
| `area_ha` | площадь |
| `geometry` | граница поля, PostGIS geometry |
| `center` | центр поля |
| `ndvi`, `ndmi`, `ndre` | карточные последние показатели |
| `metadata` | дополнительные данные |

### `field_service.scenes`

Сцены спутниковых данных.

Важные поля:

| Колонка | Смысл |
|---|---|
| `id` | UUID сцены |
| `sensor` | `s1` или `s2` |
| `captured_at` | дата/время съемки |
| `cloud_percent` | облачность, если применимо |
| `metadata` | дополнительные сведения |

### `raster_service.assets`

Ключевая таблица для raster-данных.

Важные поля:

| Колонка | Смысл |
|---|---|
| `id` | UUID asset |
| `scene_id` | ссылка на сцену |
| `kind` | тип asset |
| `index_key` | индекс/слой |
| `bucket` | S3 bucket |
| `object_key` | путь внутри bucket |
| `metadata` | fieldId, sensor, capturedOn, group, relativePath |

### `field_service.soil_profiles`

Почвенный профиль поля.

Там лежат summary, units, polygons, recommendations и raw response.

### `field_service.weather_snapshots`

Кеш погодных данных по полям.

Важные поля:

| Колонка | Смысл |
|---|---|
| `provider` | источник, например Open-Meteo |
| `mode` | forecast/archive |
| `start_date`, `end_date` | диапазон |
| `payload` | нормализованная погодная сводка |
| `raw_response` | исходный ответ провайдера |

## 19. Полезные SQL-запросы

Подключиться к базе:

```bash
docker compose --env-file .env.example exec -T postgres psql -U agrometrics -d agrometrics
```

Проверить поля:

```sql
SELECT external_id, name, crop_key, area_ha, status, ndvi, ndmi, ndre
FROM field_service.fields
WHERE external_id IN ('23:27:1101000:1039','23:27:1101000:1040','23:27:1101000:1041')
ORDER BY external_id;
```

Посчитать assets по сенсорам:

```sql
SELECT metadata->>'sensor' AS sensor, count(*)
FROM raster_service.assets
WHERE metadata->>'fieldId' IN ('23:27:1101000:1039','23:27:1101000:1040','23:27:1101000:1041')
GROUP BY metadata->>'sensor'
ORDER BY count(*) DESC;
```

Посчитать индексы Sentinel-2:

```sql
SELECT index_key, count(*)
FROM raster_service.assets
WHERE metadata->>'sensor' = 'Sentinel-2-L2A'
  AND metadata->>'group' = 'raw_indexes'
  AND metadata->>'fieldId' = '23:27:1101000:1040'
GROUP BY index_key
ORDER BY index_key;
```

Посчитать индексы Sentinel-1:

```sql
SELECT index_key, count(*)
FROM raster_service.assets
WHERE metadata->>'sensor' = 'Sentinel-1-GRD'
  AND metadata->>'group' = 'raw_indexes'
  AND metadata->>'fieldId' = '23:27:1101000:1040'
GROUP BY index_key
ORDER BY index_key;
```

Получить S3 path для конкретных NDVI:

```sql
SELECT
  metadata->>'fieldId' AS field_id,
  metadata->>'capturedOn' AS captured_on,
  index_key,
  bucket,
  object_key
FROM raster_service.assets
WHERE metadata->>'fieldId' = '23:27:1101000:1040'
  AND metadata->>'sensor' = 'Sentinel-2-L2A'
  AND metadata->>'group' = 'raw_indexes'
  AND index_key = 'NDVI'
ORDER BY captured_on;
```

Получить GeoJSON границ:

```sql
SELECT external_id, ST_AsGeoJSON(geometry)::json AS geometry
FROM field_service.fields
WHERE external_id = '23:27:1101000:1040';
```

## 20. Что такое VRA в этом пакете

`VRA` здесь означает Variable Rate Application, то есть карта-задание для дифференцированного внесения.

Файлы:

```text
metadata/vra/vra_grid_23-27-1101000-1039.json
metadata/vra/vra_grid_23-27-1101000-1040.json
metadata/vra/vra_grid_23-27-1101000-1041.json
metadata/vra/vra_summaries.json
```

Внутри `vra_grid_*.json` есть ячейки:

```json
{
  "zone": 2,
  "waterStatus": "normal",
  "corners": [[45.0, 38.0], [45.0, 38.1]]
}
```

Семантика зон:

| zone | Смысл |
|---:|---|
| 0 | слабая зона |
| 1 | ниже нормы |
| 2 | норма |
| 3 | сильная зона |
| 4 | засуха / текущий водный стресс |
| 5 | переувлажнение или текущее подтопление |
| 6 | после подтопления / исторический ущерб |
| 7 | нет данных |

Семантика `waterStatus`:

| waterStatus | Смысл |
|---|---|
| `normal` | водный режим без явной проблемы |
| `dry_stress` | водный стресс / засуха |
| `wet_stress` | переувлажнение |
| `flooded` | текущее затопление |
| `post_flood_damage` | возможный след старого затопления |
| `no_data` | недостаточно данных |

Важный агрономический момент: если зона помечена как `post_flood_damage`, ИИ не должен автоматически советовать «дать больше удобрений». Сначала нужно рекомендовать осмотр, потому что часть растений могла погибнуть, и увеличение нормы может быть бессмысленным.

## 21. Почвенные данные

Почвенные данные лежат здесь:

```text
metadata/soil/soil_profiles.json
```

И в базе:

```text
field_service.soil_profiles
field_service.soilgrids_point_cache
```

На текущем этапе это не лабораторный химанализ, а модельный/справочный почвенный слой. Его хорошо использовать как контекст:

- тип почвы;
- текстурный состав;
- органический углерод;
- pH;
- CEC;
- ориентировочные свойства горизонтов.

Но нельзя выдавать его за точный агрохимический анализ конкретных проб. Если в будущем появится история химанализа, ее нужно использовать как более надежный источник по питанию.

## 22. Погодные данные

Погодные данные лежат здесь:

```text
metadata/weather/weather_latest_by_field.json
metadata/weather/weather_snapshots_index.jsonl
```

И в базе:

```text
field_service.weather_snapshots
```

Они полезны для:

- объяснения текущих ограничений работ;
- проверки окон для опрыскивания и КАС;
- учета осадков, ветра, порывов, температуры, влажности;
- связи водного стресса с погодой.

Для ИИ важно не противоречить цифрам. Если в данных указан ветер 3.4 м/с, а предупреждение говорит о порывах до 13 м/с, надо различать средний ветер и порывы. Это разные показатели.

## 23. Как сделать первый baseline для ИИ

Хорошая первая задача: «сводка по полю».

Вход:

- поле из `fields.geojson`;
- последние значения NDVI/NDMI/NDRE;
- сезонная динамика из `sampled_statistics`;
- Sentinel-1 RVI/VV/VH как дополнительная устойчивость к облакам;
- почвенный профиль;
- погода;
- VRA summary.

Выход:

```json
{
  "fieldId": "23:27:1101000:1040",
  "summary": "Поле в целом ровное, но ...",
  "risks": [
    {
      "type": "water_stress",
      "severity": "medium",
      "evidence": ["NDMI ниже сезонной нормы", "осадков мало"]
    }
  ],
  "recommendedActions": [
    "Проверить южную часть поля",
    "Не планировать опрыскивание при порывах выше порога"
  ],
  "dataQuality": {
    "s2CloudMasked": true,
    "s1Available": true,
    "soilSource": "SoilGrids"
  }
}
```

Главная задача ИИ — не просто пересказать цифры, а объяснить причинную картину:

```text
где проблема -> чем подтверждается -> насколько уверены -> что делать агроному
```

## 24. Что не стоит делать в первой версии ИИ

Не стоит:

- обучать модель на `color_indexes` вместо `raw_indexes`;
- смешивать Sentinel-1 и Sentinel-2 без нормализации и пояснения физического смысла;
- считать облачные пиксели Sentinel-2 реальными данными;
- применять облачную маску к Sentinel-1;
- выдавать SoilGrids за лабораторный химанализ;
- давать точную норму удобрения без агрохимии, культуры, фазы, плана урожайности и ограничений хозяйства;
- обещать причинность там, где есть только корреляция;
- игнорировать `no_data`.

## 25. Как собрать признаки для ML/RAG

Для RAG/LLM:

- использовать `fields.geojson` как описание объекта;
- использовать `assets_catalog.jsonl` как retrieval index;
- использовать `sampled_statistics` как компактный числовой контекст;
- использовать `soil_profiles`, `weather`, `vra_summaries` как текстово-числовой контекст.

Для ML:

- строить временные ряды по `fieldId + sensor + indexKey + capturedOn`;
- агрегировать raster по полю: mean, median, p05, p95, std, доля no-data;
- отдельно хранить флаги качества S2: clouds/shadows/water/snow;
- отдельно хранить Sentinel-1 признаки;
- делать features не только по последней дате, но и по окнам: 7/14/30 дней, начало сезона, пик NDVI, восстановление после стресса.

Пример feature table:

| fieldId | date | ndvi_mean | ndmi_mean | ndre_mean | rvi_mean | cloud_share | soil_ph | rain_7d | zone |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 23:27:...:1040 | 2026-06-16 | 0.62 | 0.18 | 0.31 | 0.44 | 0.08 | 7.1 | 12.4 | 2 |

## 26. Как понять, что данные загружены корректно

Проверка 1: counts совпали.

```bash
scripts/verify_local.sh /path/to/project
```

Проверка 2: в базе есть Sentinel-1.

```sql
SELECT metadata->>'sensor', count(*)
FROM raster_service.assets
GROUP BY metadata->>'sensor'
ORDER BY count(*) DESC;
```

Ожидаемо для subset:

```text
Sentinel-2-L2A    12832
Sentinel-1-GRD     4224
empty                26
```

Проверка 3: конкретный S3 object существует.

```bash
docker compose --env-file .env.example run --rm --no-deps --entrypoint /bin/sh minio-init -lc '
  mc alias set local http://minio:9000 "$S3_ACCESS_KEY" "$S3_SECRET_KEY"
  mc stat "local/$S3_RAW_BUCKET/sentinel/11111111-1111-1111-1111-111111111111/6953d806-500d-4945-9567-8e0c2a3b027f/output/Sentinel-1-GRD/2026-01-01/raw_indexes/RVI.tif"
'
```

Проверка 4: локальный файл есть в пакете.

```text
s3/agrometrics-raw/sentinel/11111111-1111-1111-1111-111111111111/6953d806-500d-4945-9567-8e0c2a3b027f/output/Sentinel-1-GRD/2026-01-01/raw_indexes/RVI.tif
```

## 27. Почему есть и SQL, и JSON/JSONL

SQL нужен, чтобы восстановить систему целиком:

- frontend увидит поля;
- API сможет отдавать assets;
- tile-api сможет читать raster по `assetId`;
- MinIO будет содержать файлы по ожидаемым `objectKey`.

JSON/JSONL нужен, чтобы ИИ-разработчик мог быстро работать без всей системы:

- прочитать каталог;
- собрать датасет;
- построить прототип;
- не писать SQL на первом шаге.

Иными словами:

```text
SQL + MinIO = восстановить приложение
JSON/JSONL + s3 folder = быстро делать аналитику/ИИ
```

## 28. Как работает `seed_3_fields.sql`

Файл:

```text
db/seed_3_fields.sql
```

Он:

1. Включает `ON_ERROR_STOP`, чтобы импорт останавливался на первой реальной ошибке.
2. Создает расширения `postgis` и `pgcrypto`, если их нет.
3. Создает недостающие схемы `iam`, `field_service`, `raster_service`, `job_service`, `audit`.
4. Создает enum-типы `field_service.field_status` и `job_service.job_status`, если их нет.
5. Создает минимально нужные таблицы и индексы, если проектные миграции еще не применялись.
6. Удаляет из базы старые записи, связанные именно с этими тремя полями.
7. Вставляет organization, memberships, crops.
8. Вставляет поля с исходными UUID и PostGIS geometry.
9. Вставляет scenes.
10. Вставляет raster assets.
11. Вставляет soil profiles, weather snapshots, jobs.
12. Делает `ANALYZE` для обновления статистики Postgres.

Он не должен удалять всю базу. Он работает только с переносимым subset.

Если раньше была ошибка вида:

```text
ERROR: schema "field_service" does not exist
```

значит seed запускали на базе без базовой схемы. В актуальной версии handoff это исправлено: bootstrap встроен прямо в `seed_3_fields.sql`. Отдельно запускать проектную миграцию перед seed больше не обязательно.

## 29. Типовые проблемы и решения

### Docker не запущен

Симптом:

```text
Cannot connect to the Docker daemon
```

Решение: запустить Docker Desktop и повторить импорт.

### Порт занят

Симптом: Postgres/MinIO не стартуют.

Решение: проверить, не запущен ли другой Postgres/MinIO на тех же портах. В проекте используются:

```text
5432  PostgreSQL
9100  MinIO S3
9101  MinIO Console
```

### В базе есть assets, но файлы не открываются

Скорее всего, импортировали SQL, но не загрузили `s3/agrometrics-raw` в MinIO.

Нужно запустить:

```bash
scripts/import_local.sh /path/to/project
```

или вручную выполнить `mc mirror`.

### Sentinel-1 «нет»

Проверить:

```sql
SELECT metadata->>'sensor', count(*)
FROM raster_service.assets
WHERE metadata->>'fieldId' IN ('23:27:1101000:1039','23:27:1101000:1040','23:27:1101000:1041')
GROUP BY metadata->>'sensor';
```

Sentinel-1 должен быть как `Sentinel-1-GRD`.

### Raster есть, но значения странные

Возможные причины:

- читается `color_indexes`, а не `raw_indexes`;
- не применена маска облаков/теней для S2;
- перепутаны Sentinel-1 и Sentinel-2 шкалы;
- читается визуализированный TIFF вместо численного индекса.

## 30. Минимальный план работ для ИИ-разработчика

1. Импортировать пакет через `scripts/import_local.sh`.
2. Запустить `scripts/verify_local.sh`.
3. Прочитать `manifest_full.json`.
4. Прочитать `metadata/assets/assets_catalog.jsonl`.
5. Собрать простой dataframe: `fieldId`, `date`, `sensor`, `indexKey`, `path`.
6. Добавить статистики из `sampled_statistics`.
7. Добавить soil/weather/VRA summaries.
8. Сделать первый генератор сводки по полю.
9. Отдельно проверить Sentinel-1 признаки.
10. Описать, какие признаки реально используются, а какие пока только доступны.

## 31. Что считать хорошим результатом первой ИИ-интеграции

Хороший MVP ИИ должен:

- выбрать поле;
- показать, какие данные доступны;
- объяснить последние изменения индексов;
- учитывать облака/no-data;
- учитывать Sentinel-1 как fallback/дополнение;
- учитывать почву и погоду как контекст;
- объяснить VRA-зоны человеческим языком;
- честно писать, где данных недостаточно;
- формировать практичные действия для агронома.

Плохой MVP:

- пересказывает только NDVI;
- игнорирует маски;
- не различает оптические и радарные данные;
- дает уверенные рекомендации без источников;
- не умеет показать evidence.

## 32. Главная мысль

Эта выгрузка — не просто набор файлов. Это маленькая воспроизводимая копия производственного контура данных:

```text
поле -> сцена -> asset в Postgres -> GeoTIFF в MinIO -> статистика/карта/ИИ-вывод
```

Если ИИ-разработчик понял эту цепочку, он сможет:

- находить нужные снимки;
- связывать их с полем и датой;
- читать численные индексы;
- не путать визуальные слои с аналитическими;
- объяснять агроному не только «что видно», но и «почему мы так думаем».
