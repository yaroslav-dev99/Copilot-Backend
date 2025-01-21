from util.mongo import get_next_sequence_val
from util.misc import utc_now
from config import Config
from mongoengine import *

class TriggerRecord(Document):
    meta = {
        "strict": True,
        "indexes": [
            {"fields": ["tr_id"], "unique": True}
        ]
    }
    tr_id = LongField(required = True, default = 0) # Unique ID of trigger record
    ms_id = StringField(required = True, default = "") # Memberstack ID of user
    li_id = LongField(required = True, default = 0) # Live interview ID
    chat = StringField(required = True, default = "") # Chat
    answer = StringField(required = True, default = "") # Answer
    model = StringField(required = True, default = "") # LLM model
    is_auto = BooleanField(required = True, default = False) # True if auto trigger
    created_at = DateTimeField(required = True, default = utc_now) # Created time

    @staticmethod
    def create(ms_id: str, li_id: int, chat: str, answer: str, model: str, is_auto: bool):
        tr = TriggerRecord(
            tr_id = get_next_sequence_val("tr_id_seq"),
            ms_id = ms_id,
            li_id = li_id,
            chat = chat,
            answer = answer,
            model = model,
            is_auto = is_auto
        )
        return tr
