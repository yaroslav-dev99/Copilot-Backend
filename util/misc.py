from datetime import datetime, timezone
from config import Config
import base64

def utc_now():
    return datetime.now(timezone.utc)

def t2str(t, fmt = "%Y-%m-%d %H:%M:%S"):
    return t.strftime(fmt)

def s2time(s, fmt = "%Y-%m-%d %H:%M:%S"):
    return datetime.strptime(s, fmt)
