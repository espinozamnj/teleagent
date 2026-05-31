import os
import re
import yaml
import logging
import datetime
from teleagent.core import state

def escape_markdown(text):
    escape_chars = r"\_*[]()~`>#+-=|{}.!-"
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

def escape_markdown_code(text):
    return text.replace('\\', '\\\\').replace('`', '\\`')

def log_invalid_access(user_id, username_tg, action):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S") + f".{int(now.microsecond / 10000):02d}"
    log_msg = f"{timestamp} - ID: {user_id}, Username: {username_tg}, Action: {action}"

    if not state.LOG_DIR:
        print(f"[INVALID ACCESS] {log_msg}")
        return

    try:
        log_path = os.path.join(state.LOG_DIR, "invalid-users.log")
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_msg + "\n")
    except Exception as e:
        logging.error(f"Error saving invalid_access: {e}")

def log_history(chat_id, raw_msg, final_user, expanded_msg, status):
    now_str = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
    expanded = expanded_msg if expanded_msg else '""'
    line = f"{now_str};;;;{raw_msg};;;;{final_user};;;;{expanded};;;;{status}\n"

    if not state.LOG_DIR:
        print(f"[HISTORY {chat_id}] {line.strip()}")
        return

    try:
        history_dir = os.path.join(state.LOG_DIR, "history")
        if not os.path.exists(history_dir):
            try:
                os.mkdir(history_dir)
            except Exception as e:
                logging.error(f"Error creating history directory: {e}")
                return

        filepath = os.path.join(history_dir, f"{chat_id}.log")

        write_header = not os.path.exists(filepath)

        headers = ["Date", "Raw Command", "Target User", "Expanded Command", "Status"]
        with open(filepath, 'a', encoding='utf-8') as f:
            if write_header:
                f.write(";;;;".join(headers) + "\n")
            f.write(line)
    except Exception as e:
        logging.error(f"Error writing to history log: {e}")

def load_user_settings(username):
    yaml_path = f"/home/{username}/.config/teleagent/config.yaml"
    settings = {'aliases': {}, 'paths': []}
    try:
        if os.path.isfile(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                if 'aliases' in data:
                    settings['aliases'] = data.get('aliases', {})
                if 'paths' in data:
                    settings['paths'] = data.get('paths', [])
    except Exception as e:
        logging.error(f"Error loading config for {username}: {e}")
    return settings

def is_last_minute_command(command: str) -> bool:
    stripped = command.strip()
    match = re.match(r'^(?:sudo\s+)?(\S+)', stripped)
    if match:
        return match.group(1) in state.LAST_MINUTE_COMMANDS
    return False
