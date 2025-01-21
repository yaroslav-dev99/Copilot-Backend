from util.mongo import get_next_sequence_val
from util.misc import utc_now
from datetime import datetime
from mongoengine import *
from config import Config
import random

class Ospace(Document):
    meta = {
        "strict": True
    }
    os_id = LongField(required = True, default = 0) # Unique ID of OCRSpace
    key = StringField(required = True, default = "") # OCR key
    created_at = DateTimeField(required = True, default = utc_now) # Created time
    start_at = DateTimeField(required = True, default = utc_now) # Start time
    closed = BooleanField(required = True, default = False) # True if closed
    
    def __str__(self):
        return f"Ospace({self.key})"

    @staticmethod
    def create(key: str, start_at: datetime):
        ospace = Ospace(
            os_id = get_next_sequence_val("os_id_seq"),
            key = key,
            start_at = start_at
        )
        return ospace

    @staticmethod
    def get_key():
        opens = list(Ospace.objects(closed = False, start_at__lt = utc_now()))

        if len(opens) > 0:
            return random.sample(opens, 1)[0].key
        else:
            return Config.DEFAULT_OCR_KEY
