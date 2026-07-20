import psycopg2
import json
from src.config import DB_CONFIG

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_field_context(field_id_external: str) -> str:
    """
    Получает агрегированный контекст о поле для промпта LLM.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Получаем поле по external_id
    cur.execute("""
        SELECT id, external_id, crop_key, area_ha, ndvi, ndmi, ndre, status
        FROM field_service.fields 
        WHERE external_id = %s
    """, (field_id_external,))
    field = cur.fetchone()
    
    if not field:
        cur.close()
        conn.close()
        return f"Данные о поле с кадастровым номером {field_id_external} не найдены."
    
    field_uuid = field[0] 
    
    # 2. Получаем последние погодные данные
    cur.execute("""
        SELECT payload->>'temperature_2m_max' as temp_max,
               payload->>'temperature_2m_min' as temp_min,
               payload->>'precipitation_sum' as precip,
               payload->>'wind_speed_10m_max' as wind_max,
               start_date, end_date
        FROM field_service.weather_snapshots 
        WHERE field_id = %s 
        ORDER BY start_date DESC LIMIT 1
    """, (field_uuid,))
    weather = cur.fetchone()
    
    # 3. Получаем почвенный профиль
    cur.execute("""
        SELECT summary
        FROM field_service.soil_profiles
        WHERE field_id = %s
        LIMIT 1
    """, (field_uuid,))
    soil = cur.fetchone()
    
    # 4. Получаем последние Sentinel-2 сцены
    cur.execute("""
        SELECT 
            metadata->>'capturedOn' as captured_on,
            metadata->>'sensor' as sensor,
            index_key
        FROM raster_service.assets
        WHERE metadata->>'fieldId' = %s
          AND metadata->>'sensor' = 'Sentinel-2-L2A'
          AND metadata->>'group' = 'raw_indexes'
          AND index_key IN ('NDVI', 'NDMI', 'NDRE')
        ORDER BY captured_on DESC
        LIMIT 6
    """, (field_id_external,))
    recent_scenes = cur.fetchall()
    
    cur.close()
    conn.close()
    
    context = {
        "field_info": {
            "external_id": field[1],
            "crop": field[2],
            "area_ha": float(field[3]) if field[3] else None,
            "status": field[7],
            "latest_indicators": {
                "ndvi": float(field[4]) if field[4] else None,
                "ndmi": float(field[5]) if field[5] else None,
                "ndre": float(field[6]) if field[6] else None,
            }
        },
        "latest_weather": {
            "period": f"{weather[4]} — {weather[5]}" if weather else "N/A",
            "temp_max": weather[0] if weather else "N/A",
            "temp_min": weather[1] if weather else "N/A",
            "precipitation_mm": weather[2] if weather else "N/A",
            "wind_max_mps": weather[3] if weather else "N/A"
        } if weather else "Данные о погоде отсутствуют",
        "soil_profile": soil[0] if soil else "Почвенный профиль не загружен",
        "recent_sentinel2_scenes": [
            {"date": s[0], "sensor": s[1], "index": s[2]} for s in recent_scenes
        ] if recent_scenes else "Свежие Sentinel-2 сцены отсутствуют"
    }
    
    return json.dumps(context, ensure_ascii=False, indent=2)