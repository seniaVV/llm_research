# Агрометрикс: полный portable handoff для ИИ-интеграции

Дата сборки: 2026-07-01  
Поля: `23:27:1101000:1039`, `23:27:1101000:1040`, `23:27:1101000:1041`

Этот пакет предназначен для передачи другому разработчику, который поднимает проект локально в Docker. Внутри есть не только метаданные, но и реальные локальные S3/MinIO объекты: GeoTIFF, маски, RGB/индексные COG/TIFF и manifest-файлы.

## Состав

- `metadata/` — компактная документация, GeoJSON, asset catalog, статистики индексов, SoilGrids/weather/VRA JSON.
- `db/seed_3_fields.sql` — idempotent self-contained SQL seed для Postgres/PostGIS. Сам создает недостающие схемы/таблицы и восстанавливает ровно эти 3 поля и связанные записи.
- `db/bootstrap_schema.sql` — отдельный bootstrap схемы для ручной отладки; обычно запускать его отдельно не нужно, потому что он уже встроен в `seed_3_fields.sql`.
- `s3/agrometrics-raw/` — реальные объекты локального S3 bucket `agrometrics-raw`.
- `s3/_object_manifest.jsonl` — manifest всех выгруженных S3-объектов.
- `s3/_object_inventory.json` — сводка по S3-объектам.
- `scripts/import_local.sh` — импорт DB + MinIO в локальный Docker-контур разработчика.
- `scripts/verify_local.sh` — быстрая проверка после импорта.
- `README_FOR_AI_INTEGRATION.md` — подробное объяснение для разработчика: что это за данные, как устроена связка Postgres/MinIO, где Sentinel-1/2, как читать assets и с чего начинать ИИ-интеграцию.

## Быстрый импорт

Из корня проекта разработчика:

```bash
./exports/agrometrics_ai_full_handoff_3_fields_20260701/scripts/import_local.sh
```

Если папка с handoff лежит отдельно от проекта:

```bash
/path/to/agrometrics_ai_full_handoff_3_fields_20260701/scripts/import_local.sh /path/to/Веб-ГИС
```

Скрипт ожидает стандартный `docker-compose.yml` и `.env.example` проекта. Если используется другой env-файл:

```bash
ENV_FILE=.env ./scripts/import_local.sh /path/to/Веб-ГИС
```

`seed_3_fields.sql` можно запускать и на пустой базе: он создает `iam`, `field_service`, `raster_service`, `job_service`, нужные enum-типы, таблицы и индексы перед импортом данных.

## Что именно импортируется

- 3 поля с исходными UUID, геометрией PostGIS и карточными атрибутами.
- 776 `field_service.scenes`.
- 17 082 `raster_service.assets`.
- 34 `field_service.weather_snapshots`.
- 3 `field_service.soil_profiles`.
- 1 `field_service.soilgrids_point_cache`.
- 32 `job_service.jobs` для истории загрузок/обработки.
- 17 082 S3-объекта в `agrometrics-raw`.

По сенсорам:

- Sentinel-2 L2A: 12 832 asset/object records.
- Sentinel-1 GRD: 4 224 asset/object records.
- Служебные manifest-записи без sensor: 26 records.

Sentinel-1 лежит в тех же каталогах `s3/agrometrics-raw/sentinel/.../output/Sentinel-1-GRD/...`. Включены `raw`, `raw_indexes`, `color_indexes` и `test_download.tiff`; ключевые S1 индексы/каналы: `VV_dB`, `VH_dB`, `RVI`, `NDpol`, `CR_lin_VH_over_VV`.

## Для ИИ-разработчика

Основная точка входа: `metadata/assets/assets_catalog.jsonl`. В каждой строке есть `assetId`, `fieldId`, `sensor`, `capturedOn`, `group`, `indexKey`, `bucket`, `objectKey`.

Локальный путь к файлу строится так:

```text
s3/{bucket}/{objectKey}
```

Например:

```text
s3/agrometrics-raw/sentinel/.../raw_indexes/NDVI.tif
```

`raw_indexes` — численные одноканальные индексы для анализа.  
`color_indexes` — визуализированные слои для карты.  
`mask_clouds`, `mask_cloud_shadows`, `mask_water`, `SCL_classes` — маски/классы доступности данных.  
Sentinel-1 не требует облачной маски.

Дополнительные готовые признаки лежат в:

- `metadata/sampled_statistics/core_index_statistics_sampled.jsonl`
- `metadata/vra/vra_grid_*.json`
- `metadata/soil/soil_profiles.json`
- `metadata/weather/weather_latest_by_field.json`

## Проверка

После импорта:

```bash
./exports/agrometrics_ai_full_handoff_3_fields_20260701/scripts/verify_local.sh
```

Скрипт проверяет counts в Postgres и доступность S3 bucket через `mc`.
