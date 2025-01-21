from entity.business_model import BusinessModel
from util.mongo import get_next_sequence_val
from mongoengine import *
from enum import Enum
import cachetools

class User(Document):
    class Status(Enum):
        Normal = 0
        Suspended = 1
        Closed = 2
        
    meta = {
        "strict": True,
        "indexes": [
            {"fields": ["ms_id"], "unique": True}
        ]
    }
    user_id = LongField(required = True, default = 0) # Unique ID of user
    ms_id = StringField(required = True, default = "") # Memberstack ID of user
    email = StringField(required = True, default = "") # Login email
    name = StringField(required = True, default = "") # User name
    ip = StringField(required = True, default = "") # User IP
    plan = EnumField(BusinessModel.Plan, required = True, default = BusinessModel.Plan.Free) # Current membership plan
    
    verified = BooleanField(required = True, default = False) # True if email was verified
    is_admin = BooleanField(required = True, default = False) # True if administravie account
    status = EnumField(Status, required = True, default = Status.Normal)

    cache_by_ms_id = cachetools.LRUCache(maxsize = 1000)
    
    def __str__(self):
        return f"User({self.ms_id},{self.email})"

    @staticmethod
    def create(ms_id: str, email: str, name: str):
        user = User(            
            user_id = get_next_sequence_val("user_id_seq"),
            ms_id = ms_id,
            email = email,
            name = name
        )
        return user

    def save(self):
        super().save()     
        User.cache_by_ms_id[self.ms_id] = self
        return self

    @staticmethod
    def get_by_ms_id(ms_id: str):
        if ms_id in User.cache_by_ms_id:
            user = User.cache_by_ms_id[ms_id]
        else:
            user = User.objects(ms_id = ms_id).first()            
            if user: User.cache_by_ms_id[ms_id] = user

        return user
