from util.mongo import get_next_sequence_val
from util.misc import utc_now
from entity.language import Language
from datetime import datetime, timezone
from mongoengine import *
from enum import Enum
import cachetools

class LiveInterview(Document):
    meta = {
        "strict": True,
        "indexes": [
            {"fields": ["li_id"], "unique": True},
            {"fields": ["ms_id"], "unique": False}
        ]
    }

    class Scenario(Enum):
        Mixed = 0
        Intro = 1
        Tech = 2
        Behavior = 3
        Freelance = 4
        Recruit = 5
        Client = 6
        Team = 7

    li_id = LongField(required = True, default = 0) # Unique ID of live interview
    ms_id = StringField(required = True, default = "") # Memberstack ID of user
    url = StringField(required = True, default = "") # Meeting link
    #role = EnumField(Role, required = True, default = Role.JobSeeker) # Type of user role
    scenario = EnumField(Scenario, required = True, default = Scenario.Mixed) # Type of live interview
    company = StringField(required = True, default = "") # Company
    position = StringField(required = True, default = "") # Position title
    lang = EnumField(Language, required = True, default = Language.English) # Language
    created_at = DateTimeField(required = True, default = utc_now) # Created time
    start_at = DateTimeField(required = True, default = utc_now) # Start time
    keywords = ListField(StringField(required = True, default = "")) # Interview keywords
    jargons = ListField(StringField(required = True, default = "")) # Interview keywords extracted from job description
    trigger = IntField(required = True, default = 0) # Number of triggers used
    limit = IntField(required = True, default = 0) # Trigger limit
    autoable = BooleanField(required = True, default = False) # True if auto hints are available
    stt = BooleanField(required = True, default = False) # True if Speech-To-Text is available
    detail = BooleanField(required = True, default = False) # True if detailed hint is available
    last_stamp = IntField(required = True, default = 0) # Last timestamp of auto hint
    dg_key = StringField(required = True, default = "") # Dgram key
    ocr_key = StringField(required = True, default = "") # OCR key
    started = BooleanField(required = True, default = False) # True if the interview was started
    finished = BooleanField(required = True, default = False) # True if the interview was finished
    user_rate = IntField(required = True, default = 0) # User's rate (how the interview was going)
    joba_rate = IntField(required = True, default = 0) # Joba's rate (how Joba was helpful)
    transcript = StringField(required = True, default = "") # Meeting transcription
    feedback = StringField(required = True, default = "") # AI feedback
    cv = StringField(required = True, default = "") # User CV
    experience = StringField(required = True, default = "") # User experience extracted from CV
    instruct = StringField(required = True, default = "") # Custom instruction
    jd = StringField(required = True, default = "") # Job description
    last_hint = StringField(required = True, default = "") # Deprecated: last hint for auto trigger
    first_trigger_at = DateTimeField(required = True, default = datetime(2000, 1, 1, tzinfo = timezone.utc)) # First trigger time
    is_auto_processing = BooleanField(required = True, default = False) # True if auto hint is generating
    is_cc = BooleanField(required = True, default = False) # True if it uses built-in CC of meeting platform

    cache_by_li_id = cachetools.LRUCache(maxsize = 1000)

    def __str__(self):
        return f"LiveInterview({self.li_id},{self.ms_id})"

    @staticmethod
    def create(ms_id: str, scenario: Scenario, company: str, position: str, start_at: datetime, keywords: list, lang: int, instruct: str, cv: str, jd: str):
        li = LiveInterview(
            li_id = get_next_sequence_val("li_id_seq"),
            ms_id = ms_id,
            scenario = scenario,
            company = company,
            position = position,
            start_at = start_at,
            keywords = keywords,
            lang = lang,
            instruct = instruct,
            cv = cv,
            jd = jd
        )
        return li

    def save(self):        
        super().save()     
        LiveInterview.cache_by_li_id[self.li_id] = self

    @staticmethod
    def get_by_li_id(li_id):
        if li_id in LiveInterview.cache_by_li_id:
            li = LiveInterview.cache_by_li_id[li_id]
        else:
            li = LiveInterview.objects(li_id = li_id).first()            
            if li: LiveInterview.cache_by_li_id[li_id] = li

        return li
