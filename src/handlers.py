from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update
from logger import logger
from enver import getenv
import states
import time
from database import Database


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отображает список всех доступных команд."""
    help_text = f"""
/set_threshold - Установить пороговый процент для срабатывания уведомлений
/set_scan_interval - Установить интервал сканирования в секундах (мин: {getenv('MIN_PUMP_INTERVAL')} секунд, макс: {getenv('MAX_PUMP_INTERVAL')} секунд)
/start_scanning - Запустить процесс сканирования
/stop_scanning - Остановить процесс сканирования
        """
    await update.message.reply_text(help_text)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Добро пожаловать в ioCryptoBot! Ознокомиться с функциями бота /help')


async def start_scanning_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    with Database() as db:
        user_pump_setting = db.fetch_by_id("user_pump_settings", 'user_id', user_id)
        if user_pump_setting and user_pump_setting[4]:
            await update.message.reply_text('Сканирование уже запущено!')
        else:
            db.upsert("user_pump_settings", "user_id", user_id, {
                "is_scan": 1,
            })
            db.commit()
            await update.message.reply_text('Сканирование запущено...')


async def stop_scanning_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    with Database() as db:
        db.upsert("user_pump_settings", "user_id", user_id, {
            "is_scan": 0,
        })
        db.commit()

        await update.message.reply_text('Сканирование остановлено!')


async def set_pump_interval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Укажите интервал в секундах, в течение которого уведомления о монете не будут приходить после предыдущего уведомления:")

    return states.SET_PUMP_INTERVAL


async def new_pump_interval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        new_interval = int(update.message.text)
        if new_interval <= int(getenv('MAX_PUMP_INTERVAL')):
            user_id = update.effective_user.id

            with Database() as db:
                db.upsert("user_pump_settings", "user_id", user_id, {
                    "pump_interval": new_interval,
                })
                db.commit()

                await update.message.reply_text(f"Установлен новый интервал сканирования: {new_interval} секунд.")

            return ConversationHandler.END
        elif new_interval < int(getenv('MIN_PUMP_INTERVAL')):
            await update.message.reply_text(f"Минимальный порог: {getenv('MIN_PUMP_INTERVAL')} секунд.")
        else:
            await update.message.reply_text(f"Превышен макс. порог! (макс: {getenv('MAX_PUMP_INTERVAL')} секунд)")
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное значение интервала в секундах!")


async def set_pump_perc_threshold_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправить сообщение при вводе команды /set_threshold."""
    await update.message.reply_text("Пожалуйста, введите новое процентное значение для срабатывания сигнала")

    return states.SET_PUMP_PERC_THRESHOLD


async def new_pump_perc_threshold_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        new_threshold = float(update.message.text)

        if 100 >= new_threshold > 0:
            user_id = update.effective_user.id
            with Database() as db:
                db.upsert("user_pump_settings", "user_id", user_id, {
                    "pump_perc_threshold": new_threshold,
                })
                db.commit()

                await update.message.reply_text(f"Установлен новый порог срабатывания: {new_threshold} %.")

            return ConversationHandler.END
        else:
            await update.message.reply_text(f"Неверный процентный диапозон!")
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное пороговое значение в процентах!")


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершить текущий диалог и вернуться в начальное состояние."""
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

