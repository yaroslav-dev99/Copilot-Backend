from util.misc import utc_now, t2str
from colorama import Fore, Style
from config import Config
import logging
import sys
import os
    
LOG_COLORS = {
    logging.DEBUG: Style.RESET_ALL,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Style.BRIGHT
}

LOG_LEVEL_SHORT = {
    logging.DEBUG: "DBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARN",
    logging.ERROR: "ERRO",
    logging.CRITICAL: "CRIT"
}

class LogFormatter(logging.Formatter):
    def __init__(self, is_color, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_color = is_color

    def format(self, record):
        record.levelname = LOG_LEVEL_SHORT.get(record.levelno, record.levelname)
        log_message = super().format(record)

        if self.is_color:            
            log_color = LOG_COLORS.get(record.levelno, Style.RESET_ALL)
            return f"{log_color}{log_message}{Style.RESET_ALL}"
        else:
            return log_message

if Config.CLOUD_WATCH:
    from botocore.exceptions import *
    import boto3

    class CloudWatchHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            
            self.client = boto3.client("logs", region_name = Config.VPS_REGION)
            self.log_group = f"{Config.PROJECT_ID}/logs"
            self.log_stream = t2str(utc_now(), "%Y-%m-%d-%H-%M-%S")
            self.sequence_token = None
            
            try:
                self.client.create_log_group(logGroupName = self.log_group)
            except self.client.exceptions.ResourceAlreadyExistsException:
                pass

            try:
                self.client.create_log_stream(logGroupName = self.log_group, logStreamName = self.log_stream)
            except self.client.exceptions.ResourceAlreadyExistsException:
                pass

        def emit(self, record):
            message = self.format(record)
            timestamp = int(record.created * 1000)

            log_event = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': [
                    {
                        'timestamp': timestamp,
                        'message': message
                    }
                ]
            }

            if self.sequence_token: log_event['sequenceToken'] = self.sequence_token

            try:
                response = self.client.put_log_events(**log_event)
                self.sequence_token = response['nextSequenceToken']
            except (NoCredentialsError, PartialCredentialsError) as e:
                print(f"cloudWatch logging error: {e}")
            except Exception as e:
                print(f"cloudWatch logging failed: {e}")

def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    Logger.logger.error("unhandled exception occurred", exc_info = (exc_type, exc_value, exc_traceback))

class Logger():
    cur_log_date_str = None

    console_handler = None
    file_handler = None
    cloud_handler = None

    logger = logging.getLogger(Config.PROJECT_ID or 'app')
    logger.setLevel(logging.DEBUG)

    sys.excepthook = log_unhandled_exception

    @staticmethod
    def init_handlers():
        if not Logger.console_handler:
            Logger.console_handler = logging.StreamHandler()
            Logger.console_handler.setLevel(logging.DEBUG)
            Logger.console_handler.setFormatter(LogFormatter(True, "[%(levelname)s %(asctime)s] -> %(message)s", datefmt = "%Y-%m-%d %H:%M:%S"))

            Logger.logger.addHandler(Logger.console_handler)
        
        if Config.FILE_WATCH:
            today_str = t2str(utc_now())[:10]

            if Logger.file_handler:
                if today_str != Logger.cur_log_date_str:                
                    Logger.logger.removeHandler(Logger.file_handler)
                    Logger.file_handler = None
            
            if not Logger.file_handler:
                Logger.cur_log_date_str = today_str
                log_path = os.path.join(Config.LOG_DIR, f"{today_str}.log")

                Logger.file_handler = logging.FileHandler(log_path, encoding = "utf-8")
                Logger.file_handler.setLevel(logging.INFO)
                Logger.file_handler.setFormatter(LogFormatter(False, "[%(levelname)s %(asctime)s] -> %(message)s", datefmt = "%Y-%m-%d %H:%M:%S"))

                Logger.logger.addHandler(Logger.file_handler)

        if Config.CLOUD_WATCH and not Logger.cloud_handler:
            Logger.cloud_handler = CloudWatchHandler()
            Logger.cloud_handler.setLevel(logging.INFO)
            Logger.cloud_handler.setFormatter(LogFormatter(False, "[%(levelname)s %(asctime)s] -> %(message)s", datefmt = "%Y-%m-%d %H:%M:%S"))

            Logger.logger.addHandler(Logger.cloud_handler)

    @staticmethod
    def d(message):
        Logger.init_handlers()
        Logger.logger.debug(message)

    @staticmethod
    def i(message):
        Logger.init_handlers()
        Logger.logger.info(message)

    @staticmethod
    def w(message):
        Logger.init_handlers()
        Logger.logger.warning(message)

    @staticmethod
    def e(message):
        Logger.init_handlers()
        Logger.logger.error(message)

    @staticmethod
    def c(message):
        Logger.init_handlers()
        Logger.logger.critical(message)
