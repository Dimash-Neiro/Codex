import json
import os
from datetime import datetime

from agents import Runner
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# import hypotheses_analysis_agent
import agent_insight_rashodi
import report_agent_M

os.environ["OPENAI_API_KEY"] = "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"


TOKEN = "8139436506:AAGh3cdl_VtJuZZbrpWeP_aM7Qhjry1UUW0"



def get_chat_history(chat_file: str):
    """ Загрузка истории чата"""
    if os.path.exists(chat_file):
        with open(chat_file, 'r', encoding='utf-8') as f:
            try:
                chat_history = json.load(f)
            except Exception:
                chat_history = []
    else:
        chat_history = []
    return chat_history



async def start(update: Update, c):
    """ Обработка команды /start """
    chat_filename = f'tg_chat_{update.effective_user.id}.json'
    if os.path.exists(chat_filename):
        os.remove(chat_filename)
    await update.message.reply_text('Привет! Я Ai агент аналитик, готова исполнить любой каприз за ваши токены)...')
async def echo(update: Update, context):
    """ Обработка текстовых сообщений и запуск анализа гипотез """

    result_text = ""
    try:
        chat_filename = f'tg_chat_{update.effective_user.id}.json'
        context = get_chat_history(chat_filename)

        context.append(
            {"content": update.message.text, "role": "user"}
        )
        await update.message.reply_text('Начала обработку запроса... ⌛')
        run_result = await Runner.run(agent_insight_rashodi.insight_anomaly_agent, context)
        await update.message.reply_text('Получила ответ от GPT, обрабатываю результат... ⌛')
        # рисует красоту
        report_result = await Runner.run(report_agent_M.report_agent, str(run_result.final_output).replace('₽', 'тенге'))
        os.makedirs(os.path.join('/home/dimashsabitov/htmls'), exist_ok=True)
        html_filename = f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.html'
        with open(f'/home/dimashsabitov/htmls/{html_filename}', 'w', encoding='utf-8') as f:
            f.write(report_result.final_output)
        await update.message.reply_text('Готово! Вот HTML-отчет: ' + f'https://agents.lombard-cabinet.kz/dimash/{html_filename}')

        # await update.message.reply_text(run_result.final_output)
        context.append(
            {"content": run_result.final_output, "role": "assistant"})
        with open(chat_filename, 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error: {e} {result_text}")
        await update.message.reply_text('Ошибка при обработке: ' + str(e))


async def set_tg_commands(application):
    """ Установка команд бота """
    commands = [
        BotCommand("start", "Перезапустить агента с очищением контекста"),
        # Добавьте свои команды здесь
    ]
    await application.bot.set_my_commands(commands)


def main():
    """ Запуск бота """
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, echo))

    app.post_init = set_tg_commands
    app.run_polling()


if __name__ == '__main__':
    main()
