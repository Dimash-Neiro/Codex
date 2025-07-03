import os
os.environ["OPENAI_API_KEY"] = "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"

from agent_coder_rashodi import code_agent
import datetime
import requests
import pandas as pd
import asyncio
import re
from agents import Agent, Runner, function_tool, ModelSettings, RunResult

async def table_output_extractor(run_result: RunResult) -> str:
    """Custom output extractor for sub‑agents that return an AnalysisSummary."""
    # The financial/risk analyst agents emit an AnalysisSummary with a `summary` field.
    # We want the tool call to return just that summary text so the writer can drop it inline.
    print('table_output_extractor')
    print(str(run_result.final_output.summary))
    return str(run_result.final_output.summary)



instruction_insight_agent = """
Ты – аналитический агент. Цель: найти инсайты и аномалии в данных о займах.
У тебя есть tool = `code_analysis_generator`, он пишет код в python pandas и запускает его (Пример запуска первой строки у 'code_analysis_generator' df = pd.read_csv('zatrati.csv'))

Порядок работы (ровно 3 итерации):
1. Сформулируй ОДИН текстовый запрос в `code_analysis_generator` (Данные у него лежат в csv файле).
2. Получи таблицу T_i и выведи её без изменений.
3. Построй агрегированную таблицу A_i (суммы, среднее, count, %, min/max), сформулируй инсайты I_i.
4. Если i<3 – составь уточняющий запрос на основе I_i и повтори шаг 1.

По завершении:

* выведи T_1, A_1, I_1, …, T_3, A_3, I_3;
* подготовь «Итоговый аналитический отчёт» (выводы, рекомендации).

После каждой итерации задавайся вопросом и раскрывай его в следующей итерации.
Формат ответа (строго, без лишнего):

1. Старт отчёта --- --- ---
2. Агрегированная таблица первой итерации:
3. Аномалии и инсайты первой итерации:
4. Агрегированная таблица второй итерации:
5. Аномалии и инсайты второй итерации:
6. Агрегированная таблица третьей итерации:
7. Аномалии и инсайты третьей итерации:
8. Итоговый аналитический отчёт:



В tool = `code_analysis_generator` есть данные по расходам.

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

Ты агент — продолжайте работать, пока запрос пользователя полностью не решён, прежде чем завершать свою сессию и /
передавать управление обратно пользователю. Завершайте свою работу только тогда, когда уверены, что задача решена.

Вы ДОЛЖНЫ тщательно планировать перед каждым вызовом функции и подробно анализировать результаты предыдущих вызовов. /
НЕ выполняйте всю задачу только последовательными вызовами функций — это может ухудшить вашу способность к решению /
задачи и аналитическому мышлению.

Учти что мы работаем в валюте тенге, не указывай рубли.
Если что-то не получилось, не выдумывай, просто верни ответ что ничего не получилось и причину.
"""


# ==== AGENT: Агент по выявлению инсайтов и аномалий ==== #
insight_anomaly_agent = Agent(
    name="Insight_and_anomaly_detection_Agent", # Агент_по_выявлению_инсайтов_и_аномалий
    instructions=instruction_insight_agent,
    model="o3",
    # model="o3-pro-2025-06-10",
    # model="gpt-4.1",

    tools = [code_agent.as_tool(
            tool_name="code_analysis_generator",
            tool_description="Агент — это разработчик-аналитик, который пишет код на Python (pandas) для анализа данных о производственном цикле, связанных с займами. После окончания  работы представляет ответ с данными строго в табличной форме. У него можешь запрашивать данные по производственному циклу",
            custom_output_extractor=table_output_extractor,
        )
    ]

)


#
# # --------------------------------------------------------------------------------------
# # 5. Пример запуска (опционально)
# # --------------------------------------------------------------------------------------
# user_query = ("Сделай глубокий анализ по зарплатам по месяцам ")
# #
# # runner = Runner(code_agent, user_query)
# # print(runner)
#
# async def main():
#     code_result = await Runner.run(insight_anomaly_agent, user_query)
#     print(type(code_result.final_output))
#     print(code_result.final_output)
#
#
# # # Запуск
# if __name__ == "__main__":
#     asyncio.run(main())
