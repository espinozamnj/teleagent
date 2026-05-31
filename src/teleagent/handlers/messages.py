import os
import re
import datetime
import subprocess
import tempfile
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from teleagent.core import state
from teleagent.utils.helpers import (
    escape_markdown_code,
    log_invalid_access,
    log_history,
    load_user_settings,
    is_last_minute_command
)

MAX_MESSAGE_LENGTH = 4000

async def _execute_and_reply(message, raw_message, target_user, command, expanded_msg, paths_list=None):
    chat_id = message.chat_id
    try:
        path_injection = ""
        if paths_list:
            valid_paths = [p for p in paths_list if os.path.isdir(p)]
            if valid_paths:
                joined_paths = ':'.join(valid_paths)
                path_injection = f'export PATH="$PATH:{joined_paths}"; '

        full_command = f"{path_injection}{command}"

        exec_cmd = ['sudo', '-u', target_user, 'bash', '-c', full_command]

        cwd = f"/home/{target_user}" if target_user != 'root' else "/root"
        if not os.path.isdir(cwd): cwd = "/"

        result = subprocess.run(
            exec_cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd
        )

        output = (result.stdout + "\n" + result.stderr).strip() if result.stderr else result.stdout.strip()
        if not output: output = "No output."

        if result.returncode == 0:
            status_code = "1" if output != "No output." else "0"
        else:
            status_code = "E"

        log_history(chat_id, raw_message, target_user, expanded_msg, status_code)

        if len(output) < MAX_MESSAGE_LENGTH:
            escaped_output = escape_markdown_code(output)
            await message.reply_text(
                f"*Result*\n```text\n{escaped_output}\n```",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_to_message_id=message.message_id
            )
        else:
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt', encoding='utf-8') as tmp_file:
                tmp_file.write(output)
                temp_file_path = tmp_file.name
            with open(temp_file_path, 'rb') as doc:
                await message.reply_document(
                    document=InputFile(doc, filename='resultado.txt'),
                    caption='The command returned a very long result.',
                    reply_to_message_id=message.message_id
                )
            os.remove(temp_file_path)

    except subprocess.TimeoutExpired:
        log_history(chat_id, raw_message, target_user, expanded_msg, "%")
        await message.reply_text("❌ Error: The command took too long and was aborted.", reply_to_message_id=message.message_id)

    except Exception as e:
        log_history(chat_id, raw_message, target_user, expanded_msg, "E")
        escaped_error = escape_markdown_code(str(e))
        msg_text = f"❌ Execution error.\n```text\n{escaped_error}```"
        await message.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN_V2, reply_to_message_id=message.message_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username_tg = update.effective_user.username
    raw_message = update.message.text.strip()

    if user_id not in state.AUTHORIZED_USERS:
        log_invalid_access(user_id, username_tg, f"Message: {raw_message}")
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    user_info = state.AUTHORIZED_USERS[user_id]
    os_user = user_info['username']
    target_user = os_user
    command = raw_message
    expanded_msg = ""

    user_settings = load_user_settings(os_user)
    user_paths = user_settings.get('paths', [])

    if raw_message.startswith('.. '):
        if user_info['root']:
            target_user = 'root'
            command = raw_message[3:].strip()
        else:
            await update.message.reply_text("❌ You do not have permissions to execute commands as root.")
            return

    elif raw_message.startswith('$'):
        match = re.match(r'^\$([a-zA-Z0-9_-]+)\s+(.*)', raw_message)
        if match:
            requested_user = match.group(1)
            if user_info['can_switch']:
                target_user = requested_user
                command = match.group(2).strip()
            else:
                await update.message.reply_text("❌ You do not have permissions to execute commands as another user.")
                return

    elif raw_message.startswith('.') and '/' not in raw_message.split(' ')[0]:
        parts = raw_message.split(' ', 1)
        shortcut = parts[0][1:]
        args = parts[1] if len(parts) > 1 else ""

        aliases = user_settings.get('aliases', {})
        if shortcut in aliases:
            expanded_msg = aliases[shortcut].replace('{args}', args)
            command = expanded_msg
        else:
            await update.message.reply_text(f"❌ The shortcut '{shortcut}' does not exist in your ~/.config/btg_control/config.yaml")
            return

    if command.startswith('sudo ') or command == 'sudo':
        if user_info['root']:
            target_user = 'root'
            command = re.sub(r'^sudo\s+', '', command)
        else:
            await update.message.reply_text("❌ This command requires 'sudo' and you do not have root privileges.")
            return

    if is_last_minute_command(command):
        state.PENDING_CONFIRMATIONS[user_id] = {
            'command': command,
            'raw_message': raw_message,
            'target_user': target_user,
            'expanded_msg': expanded_msg,
            'paths': user_paths,
            'sent_at': datetime.datetime.now(),
            'msg_obj': update.message
        }
        escaped_cmd = escape_markdown_code(command)
        escaped_target_user = escape_markdown_code(target_user)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Proceed", callback_data='lm_confirm'),
            InlineKeyboardButton("❌ Cancel", callback_data='lm_cancel'),
        ]])
        await update.message.reply_text(
            f"⚠️ Destructive command \\(User: `{escaped_target_user}`\\):\n`{escaped_cmd}`",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=keyboard,
            reply_to_message_id=update.message.message_id
        )
        return

    await _execute_and_reply(update.message, raw_message, target_user, command, expanded_msg, user_paths)
