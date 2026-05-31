import logging
import sys

class _QuietNetworkFilter(logging.Filter):
    _KEYWORDS = (
        'Temporary failure in name resolution',
        'ConnectError',
        'NetworkError',
        'Network Retry Loop',
    )

    def filter(self, record):
        if record.levelno >= logging.ERROR:
            msg = record.getMessage()
            if any(kw in msg for kw in self._KEYWORDS):
                record.levelno = logging.WARNING
                record.levelname = 'WARNING'
                record.exc_info = None
                record.exc_text = None
        return True

def setup_logging():
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        stream=sys.stdout
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.ERROR)
    logging.getLogger("telegram.ext").setLevel(logging.ERROR)

    _net_filter = _QuietNetworkFilter()
    logging.getLogger().addFilter(_net_filter)
