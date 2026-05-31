import datetime

AUTHORIZED_USERS = {}
LOG_DIR = None
CREDS_FILE = None
BOT_START_TIME = datetime.datetime.now()

LAST_MINUTE_COMMANDS = ['reboot', 'shutdown', 'halt', 'poweroff']
PENDING_CONFIRMATIONS = {}
LAST_MINUTE_TIMEOUT = 60
