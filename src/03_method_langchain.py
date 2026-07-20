from langchain_community.utilities import SQLDatabase
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import DB_CONFIG, MODEL_NAME, OPTIMAL_PARAMS

db_url = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    f"?options=-c%20search_path=field_service,raster_service,public"
)

db = SQLDatabase.from_uri(db_url)

llm_sql = ChatOllama(
    model=MODEL_NAME,
    temperature=0.0,
    top_p=OPTIMAL_PARAMS["top_p"]
)

llm_interpret = ChatOllama(
    model=MODEL_NAME,
    temperature=OPTIMAL_PARAMS["temperature"],
    top_p=OPTIMAL_PARAMS["top_p"]
)

target_tables = ["fields", "weather_snapshots", "assets"]
schema_info = db.get_table_info(table_names=target_tables)

agro_sql_prompt = PromptTemplate.from_template("""
Ты пишешь ТОЛЬКО SQL-код для PostgreSQL. Никаких слов, никаких "Примечание", никаких markdown-оберток (```sql). Только чистый текст запроса.

Схема БД:
{schema}

ПРАВИЛА:
1. Используй ТОЛЬКО таблицы из схемы выше: fields, weather_snapshots, assets.
2. Таблица `fields` содержит external_id, ndvi, ndmi. Используй external_id для фильтрации.
3. Таблица `assets` содержит JSONB-поле `metadata`. Для извлечения значений используй оператор ->>. Пример: metadata->>'sensor' = 'Sentinel-2-L2A'.
4. Таблица `weather_snapshots` содержит JSONB-поле `payload`. Пример: payload->>'precipitation_sum'.
5. Только сам запрос, без других слов                                              

ПРИМЕР ПРАВИЛЬНОГО ЗАПРОСА:
Вопрос: Покажи ndvi и ndmi для поля 23:27:1101000:1040
SQL: SELECT external_id, ndvi, ndmi FROM fields WHERE external_id = '23:27:1101000:1040';

Вопрос пользователя: {question}
SQL:
""")

sql_chain = agro_sql_prompt | llm_sql | StrOutputParser()

def ask_via_langchain(question: str):
    print("МЕТОД: LangChain Text-to-SQL")
    print(f"Вопрос: {question}")
    
    try:
        sql_query = sql_chain.invoke({"question": question, "schema": schema_info})
            
        print(f"\nСгенерированный SQL:\n{sql_query}\n")

        result = db.run(sql_query)
        print(f"Результат выполнения БД:\n{result}\n")

        interpret_prompt = f"""Пользователь задал вопрос: '{question}'. 
        База данных вернула следующие данные: {result}. 
        Объясни это простыми словами агроному, сделав акцент на рисках водного стресса. 
        Если данных нет, скажи об этом прямо."""
        
        interpretation = llm_interpret.invoke(interpret_prompt).content
        print(f"Интерпретация:\n{interpretation}")
        
    except Exception as e:
        print(f"\nОШИБКА: {e}")

if __name__ == "__main__":
    target_question = "Каково текущее состояние поля 23:27:1101000:1040 и есть ли риски водного стресса?"
    ask_via_langchain(target_question)