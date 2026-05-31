import os
import sys
import yaml
import logging
from teleagent.core import state

def load_config(config_path):
    if not os.path.isfile(config_path):
        print(f"Error: The configuration file '{config_path}' does not exist or is not a regular file.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error: Failed to read or parse the YAML file '{config_path}'. Details: {e}", file=sys.stderr)
        sys.exit(1)

    if not config:
        print("Error: The configuration file is empty or invalid.", file=sys.stderr)
        sys.exit(1)

    if 'file_tg_bot_creds' not in config:
        print("Error: Missing required key 'file_tg_bot_creds' in the configuration.", file=sys.stderr)
        sys.exit(1)

    creds_file = config['file_tg_bot_creds']
    if not os.path.isfile(creds_file) or not os.access(creds_file, os.R_OK):
        print(f"Error: The credentials file '{creds_file}' does not exist or cannot be read.", file=sys.stderr)
        sys.exit(1)

    state.CREDS_FILE = creds_file

    log_dir = config.get('log_dir')
    if log_dir:
        if not os.path.exists(log_dir):
            try:
                os.mkdir(log_dir)
            except Exception as e:
                print(f"Error: Failed to create log directory '{log_dir}'. Details: {e}", file=sys.stderr)
                sys.exit(1)
        elif not os.path.isdir(log_dir):
            print(f"Error: Log path '{log_dir}' exists but is not a directory.", file=sys.stderr)
            sys.exit(1)

        if not os.access(log_dir, os.W_OK):
            print(f"Error: Log directory '{log_dir}' is not writable.", file=sys.stderr)
            sys.exit(1)
        
        state.LOG_DIR = log_dir
    else:
        state.LOG_DIR = None

    extra_commands = config.get('confirmation_required', [])
    if isinstance(extra_commands, list):
        for cmd in extra_commands:
            if cmd not in state.LAST_MINUTE_COMMANDS:
                state.LAST_MINUTE_COMMANDS.append(cmd)

    users_dict = config.get('users', {})
    state.AUTHORIZED_USERS.clear()

    for username, data in users_dict.items():
        for tg_id in data.get('tg_ids', []):
            state.AUTHORIZED_USERS[int(tg_id)] = {
                'username': username,
                'root': data.get('root', False),
                'can_switch': data.get('can_switch', False)
            }

    logging.info(f"Configuration loaded. {len(state.AUTHORIZED_USERS)} authorized IDs.")

def get_bot_token():
    try:
        with open(state.CREDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('TG_BOT_TOKEN='):
                    return line.strip().split('=', 1)[1].strip("'\"")
    except Exception as e:
        print(f"Error: Failed to read {state.CREDS_FILE}. Details: {e}", file=sys.stderr)
        sys.exit(1)

    print("Error: TG_BOT_TOKEN not found in the credentials file.", file=sys.stderr)
    sys.exit(1)
