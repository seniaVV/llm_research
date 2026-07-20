from openai import OpenAI
from src.config import OLLAMA_BASE_URL, MODEL_NAME, OPTIMAL_PARAMS
from src.db_utils import get_field_context

client = OpenAI(base_url=f"{OLLAMA_BASE_URL}/v1", api_key="ollama")

def ask_agronomist_openai(field_id: str, question: str):
    context = get_field_context(field_id)
    
    system_prompt = """Ты опытный агроном-аналитик. Отвечай строго на основе предоставленных JSON-данных. 
    Если данных недостаточно, честно скажи об этом. Не выдумывай значения индексов.
    Обрати особое внимание на NDMI (индекс влажности) и данные об осадках при оценке водного стресса."""
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Данные о поле:\n{context}\n\nВопрос пользователя: {question}"}
        ],
        temperature=OPTIMAL_PARAMS["temperature"],
        top_p=OPTIMAL_PARAMS["top_p"],
        max_tokens=OPTIMAL_PARAMS["num_predict"]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    field = "23:27:1101000:1040"
    target_question = "Каково текущее состояние поля и есть ли риски водного стресса?"
    
    print(f"МЕТОД: OpenAI API + Psycopg2")
    print(f"Поле: {field}")
    print(f"Вопрос: {target_question}")
    
    answer = ask_agronomist_openai(field, target_question)
    print(f"\nОтвет:\n{answer}\n")