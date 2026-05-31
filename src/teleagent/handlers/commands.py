import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from teleagent.core import state
from teleagent.utils.helpers import log_invalid_access, load_user_settings

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in state.AUTHORIZED_USERS:
        u_info = state.AUTHORIZED_USERS[user_id]
        await update.message.reply_text(f"Bot active. Authenticated as {u_info['username']}.")
    else:
        log_invalid_access(user_id, update.effective_user.username, "/start")
        await update.message.reply_text("❌ You are not authorized to use this bot.")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in state.AUTHORIZED_USERS:
        return

    u_info = state.AUTHORIZED_USERS[user_id]

    msg = f"🔧 *Command Guide*\nYour default user is: `{u_info['username']}`\n\n"
    msg += "• `<command>` : Executes with your permissions\\.\n"
    msg += "• `.<alias> [args]` : Executes an alias from your personal config\\.\n"

    if u_info['root']:
        msg += "• `.. <command>` : Executes as `root`\\.\n"
    if u_info['can_switch']:
        msg += "• `$<user> <command>` : Executes as another user\\.\n"

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)

async def cmd_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in state.AUTHORIZED_USERS:
        return

    os_user = state.AUTHORIZED_USERS[user_id]['username']
    settings = load_user_settings(os_user)
    aliases = settings.get('aliases', {})

    if not aliases:
        await update.message.reply_text("You do not have any aliases configured.")
        return

    msg = "*Your Configured Aliases:*\n```yaml\n"
    for k, v in aliases.items():
        msg += f"{k}: {v}\n"
    msg += "```"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in state.AUTHORIZED_USERS:
        return

    uptime = datetime.datetime.now() - state.BOT_START_TIME

    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    msg = "🟢 *Bot Status*\n\n"
    msg += f"⏳ *Uptime:* {days}d {hours}h {minutes}m {seconds}s"

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)
