#!/usr/bin/env python
from telegram import Update
from handlers import (
    help_handler,
    start_handler,
    start_scanning_handler,
    stop_scanning_handler,
    set_pump_interval_handler,
    new_pump_interval_handler,
    set_pump_perc_threshold_handler,
    new_pump_perc_threshold_handler,
    cancel_handler,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from enver import getenv
import states
from apscheduler.schedulers.background import BackgroundScheduler
from background_worker import pump_worker, check_worker, cleaner_worker

# Создаем планировщик
scheduler = BackgroundScheduler()
scheduler.add_job(pump_worker, 'interval', seconds=30)
scheduler.add_job(check_worker, 'interval', seconds=30)
scheduler.add_job(cleaner_worker, 'interval', seconds=180)

scheduler.start()

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(getenv('BOT_TOKEN')).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))

    conv_handler_scan_interval = ConversationHandler(
        entry_points=[CommandHandler("set_scan_interval", set_pump_interval_handler)],
        states={
            states.SET_PUMP_INTERVAL: [MessageHandler(filters.Regex(r'^\d+$'), new_pump_interval_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
    )

    conv_handler_set_threshold = ConversationHandler(
        entry_points=[CommandHandler("set_threshold", set_pump_perc_threshold_handler)],
        states={
            states.SET_PUMP_PERC_THRESHOLD: [MessageHandler(filters.Regex(r'^\d+(\.\d+)?$'), new_pump_perc_threshold_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
    )

    application.add_handler(CommandHandler('start_scanning', start_scanning_handler))
    application.add_handler(CommandHandler('stop_scanning', stop_scanning_handler))
    application.add_handler(conv_handler_scan_interval)
    application.add_handler(conv_handler_set_threshold)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
