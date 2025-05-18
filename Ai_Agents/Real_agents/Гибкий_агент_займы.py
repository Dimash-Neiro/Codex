import os


import pandas as pd
import requests
from agents import Agent, Runner, function_tool
import asyncio

API_URL = "https://api.lombard-cabinet.kz/api/smartlombard-reports/sm-reports/report/operations/M4SnVvORWAxR?from=2025-01-01&to=2025-02-28"

@function_tool
def get_data():
    print(API_URL)
    response = requests.get(API_URL)
    df = pd.read_json(response.text)
    return df


code_agent = Agent(
    name="Генератор кода анализа",
    instructions="""
    Никогда не выводи результат! Не пиши текст, таблицы или ответы — только pandas-код!
    Весь анализ сохраняй в переменную result.
    Запрещены print, display, return, любые тексты вне кода.
    Код должен работать только с get_data() и pandas.
    
    Тебе доступна функция get_data(), которая возвращает pandas.DataFrame по структуре:

    _id: str — уникальный идентификатор операции
    type_operation: str — тип операции (например, 'pledge', 'buyout', 'part_buyout')
    pawn_chain_id: int — идентификатор цепочки залога
    date: datetime — дата операции

    Важно:  
    - Все операции по одному займу объединяются через поле pawn_chain_id.  
    - Один pawn_chain_id описывает жизненный цикл одного займа (от открытия до закрытия).
    - Открытие займа — операция с type_operation == 'pledge'.
    - Закрытие займа — операция с type_operation == 'buyout' по тому же pawn_chain_id (part_buyout не считать закрытием!).
    - Для расчёта срока займа: для каждого pawn_chain_id найди дату pledge (самую первую по дате) и первую дату buyout после неё.
    - Не учитывай цепочки, где нет buyout после pledge.
    - Если дата buyout раньше даты pledge — такие цепочки игнорируй.
    - Сохраняй только код — не выводи текстовый ответ, не придумывай результат, только код!
    - Сохраняй результат анализа в переменной result.

    Пример кода:
    import pandas as pd
    df = get_data()
    df['date'] = pd.to_datetime(df['date'])
    pledges = df[df['type_operation'] == 'pledge'].copy()
    closes = df[df['type_operation'] == 'buyout'].copy()
    cohort_results = []
    for chain_id in pledges['pawn_chain_id'].unique():
        pledge_dates = pledges[pledges['pawn_chain_id'] == chain_id]['date']
        buyout_dates = closes[closes['pawn_chain_id'] == chain_id]['date']
        if pledge_dates.empty or buyout_dates.empty:
            continue
        pledge_date = pledge_dates.min()
        buyout_date = buyout_dates[buyout_dates > pledge_date].min()
        if pd.isna(buyout_date):
            continue
        duration = (buyout_date - pledge_date).days
        if duration < 0:
            continue
        month = pledge_date.to_period('M').strftime('%Y-%m')
        cohort_results.append({'month': month, 'duration': duration})
    if not cohort_results:
        result = "Нет закрытых займов с корректными датами в данных."
    else:
        result_df = pd.DataFrame(cohort_results)
        table = (
            result_df
            .groupby('month')
            .agg(avg_duration=('duration', 'mean'), count=('duration', 'count'))
            .reset_index()
        )
        table['avg_duration'] = table['avg_duration'].round(1)
        result = table.to_string(index=False, header=["Месяц", "Средний срок займа (дней)", "Кол-во займов"])
    """,
    tools=[get_data]
)



@function_tool
def execute_code(code: str):
    import pandas as pd
    local_vars = {}
    try:
        exec(code, {"get_data": get_data, "pd": pd}, local_vars)
        result = local_vars.get('result')
        # Всегда возвращаем только результат исполнения кода!
        if isinstance(result, pd.DataFrame):
            return result.to_string()
        return str(result)
    except Exception as e:
        return f"Ошибка выполнения кода: {e}"

executor_agent = Agent(
    name="Исполнитель кода",
    instructions="""
    Выполни предоставленный pandas-код для анализа данных и верни только результат исполнения.
    Обязательно используй tool 'execute_code'.
    Не пиши ничего от себя, возвращай только вывод result!
    """,
    tools=[execute_code]
)



async def main():
    user_query = """
    Построй таблицу средних сроков займа по месяцам.
    Месяцем считать месяц выдачи займа (pledge), считать только те займы, которые закрыты через buyout.
    """
    # Code Agent генерирует только pandas-код!
    code_result = await Runner.run(code_agent, user_query)
    generated_code = code_result.final_output
    print("🐍 Сгенерированный код:\n", generated_code)

    # Executor Agent запускает код и возвращает только результат исполнения
    exec_result = await Runner.run(executor_agent, generated_code)
    print("\n📊 Результат анализа:\n", exec_result.final_output)

if __name__ == "__main__":
    asyncio.run(main())


