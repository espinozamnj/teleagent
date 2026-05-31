#!/usr/bin/env python3

import argparse
import logging
import sys
import os
from telegram import BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import NetworkError

from teleagent.core.logger import setup_logging
from teleagent.core.config import load_config, get_bot_token
from teleagent.core.version import get_version_message
from teleagent.handlers.commands import cmd_start, cmd_help, cmd_alias, cmd_status
from teleagent.handlers.messages import handle_message
from teleagent.handlers.callbacks import handle_confirmation_callback

async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Show bot greeting"),
        BotCommand("help", "Show syntax guide"),
        BotCommand("alias", "Show your aliases from config.yaml"),
        BotCommand("status", "Show bot status")
    ])

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, NetworkError):
        return
    logging.error("Error in update %s: %s", update, context.error)

def main():
    parser = argparse.ArgumentParser(
        description="Telegram Command Bot",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-v', '--version', action='version', version=get_version_message())
    parser.add_argument('--config', required=True, help='Path to the main config.yaml file')
    args = parser.parse_args()

    if hasattr(os, 'geteuid') and os.geteuid() != 0:
        print("Error: This program must be run with root privileges (using sudo).", file=sys.stderr)
        sys.exit(1)

    setup_logging()

    load_config(args.config)
    bot_token = get_bot_token()

    app = ApplicationBuilder().token(bot_token).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("alias", cmd_alias))
    app.add_handler(CommandHandler("status", cmd_status))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(handle_confirmation_callback, pattern='^lm_(confirm|cancel)$'))

    app.add_error_handler(global_error_handler)

    logging.info("Bot started...")
    app.run_polling(poll_interval=5.0)
    logging.info("Bot stopped cleanly.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Bot stopped cleanly.")
        sys.exit(0)
    except SystemExit as e:
        if e.code == 0:
            logging.info("Bot stopped cleanly.")
        sys.exit(e.code)
    except Exception as e:
        logging.error("Fatal error starting the bot: %s", e)
        sys.exit(1)