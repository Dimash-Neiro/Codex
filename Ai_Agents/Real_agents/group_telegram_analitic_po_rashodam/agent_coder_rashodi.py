import os
os.environ["OPENAI_API_KEY"] = "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"


import datetime
import io
import contextlib
import requests
import pandas as pd
import asyncio
import re
import numpy as np
from agents import Agent, Runner, function_tool, ModelSettings
from pydantic import BaseModel, field_validator

# --------------------------------------------------------------------------------------
# 1. Тип результата ─ строго таблица (list[dict]), никакого текста
# --------------------------------------------------------------------------------------
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from pydantic import BaseModel, field_validator
from typing import List, Dict, Any
import json
# ==== Тип результата ====
class TableOutput(BaseModel):
    summary: str
    """Текстовое описание таблицы-результата анализа. """


# --------------------------------------------------------------------------------------
# 2. Инструмент (tool)
# --------------------------------------------------------------------------------------
#  cache DataFrame между вызовами, чтобы не перечитывать огромный CSV
import contextlib, io, json, pandas as pd, re, datetime, requests

_DF_CACHE = None

@function_tool
def run_code(code: str) -> str:
    """
    Выполняет Python‑код пользователя над DataFrame `df` и возвращает
    JSON‑строку orient='records'.
    """
    global _DF_CACHE
    if _DF_CACHE is None:
        _DF_CACHE = pd.read_csv('zatrati_po_01_07_2025.csv')
    df = _DF_CACHE.copy()
    df['Дата'] = pd.to_datetime(df['Дата'], errors='coerce')
    # фильтрация с ноября 2024 года
    df = df[df['Дата'] >= pd.Timestamp('2024-11-01')]

    code_clean = re.sub(r"```(?:python)?", "", code).strip()
    local_vars = {'df': df}

    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(code_clean, {"pd": pd, "requests": requests, "datetime": datetime}, local_vars)

        result = local_vars.get("result", None)

        if isinstance(result, pd.DataFrame):
            result_df = result
        elif isinstance(result, pd.Series):
            result_df = result.to_frame(name=result.name or "value")
        elif isinstance(result, (list, tuple)):
            result_df = pd.DataFrame(result)
        elif isinstance(result, dict):
            result_df = pd.DataFrame([result])
        elif isinstance(result, (int, float, str, bool)):
            result_df = pd.DataFrame([{"value": result}])
        else:
            result_df = pd.DataFrame(
                [{"error": "Unsupported result type", "type": str(type(result))}]
            )

    except Exception as e:
        result_df = pd.DataFrame([{"error": str(e), "code_attempted": code_clean}])

    # ← сериализуем в JSON‑строку
    return result_df.to_json(orient="records", force_ascii=False)


# --------------------------------------------------------------------------------------
# 3. Инструкции для агента (system prompt)
# --------------------------------------------------------------------------------------

# Ты разработчик‑аналитик данных.
# Твоя задача — писать на Python (pandas) код, который анализирует DataFrame `df`.
#
# Правила:
# 1. Передавай готовый код в инструмент `run_code`.
# 2. После выполнения кода переменная `result` ДОЛЖНА содержать итог анализа.
# 3. Никакого текстового вывода, комментариев или описаний — только таблица (DataFrame/Series/список/словарь/скаляр).
# 4. Работай, пока задача пользователя не решена; завершай сессию, только убедившись, что получилась нужная таблица.
instructions_code_agent = """
Ты senior разработчик, аналитик который пишет код на Python (pandas) для анализа данных.
1. Твоя задача — создавать код на Python для анализа предоставленного набора данных (используй библиотеку pandas).
2. После каждого логического блока добавляй print().
3. Передавай итоговый код в инструмент 'run_code'.
4. В конце выдай результат в таблице, а ниже текст с разъяснениями.
5. Анализируй всегда агрегированные данные.

# Ты агент — продолжайте работать, пока запрос пользователя полностью не решён, прежде чем завершать свою сессию и /
# передавать управление обратно пользователю. Завершайте свою работу только тогда, когда уверены, что задача решена.
# 
# Вы ДОЛЖНЫ тщательно планировать перед каждым вызовом функции и подробно анализировать результаты предыдущих вызовов. /
# НЕ выполняйте всю задачу только последовательными вызовами функций — это может ухудшить вашу способность к решению /
# задачи и аналитическому мышлению.

В инструменте 'run_code' уже реализована загрузка и предобработка данных, тебе не нужно писать этот код. Работай с переменной df (pandas DataFrame).


Описание структуры данных по расходам (основные поля/названия столбцов):
<Описание_структуры>
ApiField(field_name="Дата", data_type="string", example="2025-07-01", description="Дата совершения операции", additional_info="Дата указана в формате YYYY-MM-DD"),
ApiField(field_name="Операция", data_type="string", example="Расход (затраты)", description="Тип финансовой операции", additional_info="Можно не использовать для аналитики"),
ApiField(field_name="Описание", data_type="string", example="Freedom Life (-15%) страховка Перезалог ЕС013291", description="Описание и назначение произведенной операции", additional_info=""),
ApiField(field_name="Сумма", data_type="float", example=383.0, description="Сумма денежных средств операции", additional_info="Сумма указана в тенге"),
ApiField(field_name="Отделение", data_type="string", example="Х Кемель ID-8195", description="Название отделения, в котором была совершена операция", additional_info="Те отделения, у которых есть отдельно стоящий'Х ' или указан 'с правом ношения', относятся к продукту СПН (зай с правом ношения)"),
ApiField(field_name="Сотрудник", data_type="string", example="БотК.Х.", description="Сотрудник, проводивший операцию", additional_info="Учтите, что это только тот ктно внес операцию, по этому пункту лучше не считать аналитику, если нет прямого на это запроса"),
ApiField(field_name="Категория", data_type="string", example="Freedom Life (-15%) страховка", description="Категория, к которой отнесена операция", additional_info="Список категорий: ['Freedom Life (-15%) страховка', 'Хоз. товары','Комиссия за банковские операции', 'Выдача зарплаты', 'Дорожные','Заправка принтера', 'Аренда помещения', '% за рассрочку банку','Чистка и ремонт ювелирных изделий','Юридические и консалтинговые услуги', 'Рабочая техника',
       'Покупка оборудования', 'Оплата интернета',
       'Программное обеспечение', 'Корректировочные расходы',
       'Пополнение баланса на рабочий',
       'Услуги уборщицы, электрика, сантехника', 'Коммисия Kaspi',
       'Ремонт товаров', 'Покупка канцтоваров', 'Коммунальные услуги',
       'Продукты питания', 'Неизвестно', 'Охрана', 'Реклама', 'Налоги',
       'Обучение', 'Выемка', 'Банк', 'Прочие расходы', 'Покупка воды',
       'Возврат долга', 'Ремонт телефонов', 'Открытие нового отделения']"),
ApiField(field_name="Должность", data_type="string", example="Ахо", description="Если был расход по зарплате, то тут указывается должность сотрудника, который получил зарплату", additional_info="Не польный список должностей: ['Ахо', 'Неизвестно', 'Оценщик', 'Юрист', 'Директор', 'Магазин Loona', 'аудитор', 'Hr', 'Аналитик', 'Бухгалтерия','Ген. дир.', 'Видеограф', 'Программист', 'Казначей','Отдел взыскания', 'Колл-центр', 'Роп', '(E-commerce)', 'Smm','Отдел обучения'] Может принимать значение 'Неизвестно', если должность не определена")
</Описание_структуры>





⚠️ **Важное требование к твоему коду:**

- **Результат выполнения кода** всегда сохраняй в специальной переменной **`result`**.
- Это обязательное условие: переменная `result` используется системой для извлечения итогового значения после выполнения твоего кода.

Взаимодействуй со своим tool run_code столько раз, сколько нужно чтобы полноценно ответить на запрос пользлвателя.
Не придумывай дополнительные данные которые не указаны в описании данных.

"""

# --------------------------------------------------------------------------------------
# 4. Определяем агента
# --------------------------------------------------------------------------------------
code_agent = Agent(
    name="code_analysis_generator",
    instructions=instructions_code_agent,
    # model="o3",
    model="gpt-4.1",
    # model="o3-pro-2025-06-10",

    tools=[run_code],
    output_type=TableOutput,
)
#
# # --------------------------------------------------------------------------------------
# # 5. Пример запуска (опционально)
# # --------------------------------------------------------------------------------------
# user_query = ("Подсчитай сумму расходов по месяцам за 2025 год. Изучи глубоко почему идет прирост в расходах по зарплатам")
# #
# # runner = Runner(code_agent, user_query)
# # print(runner)
#
# async def main():
#     code_result = await Runner.run(code_agent, user_query)
#     print(type(code_result.final_output))
#     print(code_result.final_output.summary)
#
#
# # # Запуск
# if __name__ == "__main__":
#     asyncio.run(main())





