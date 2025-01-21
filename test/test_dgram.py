import os
os.sys.path.append(os.getcwd())

from util.mongo import *
from entity.dgram import Dgram
from util.misc import utc_now

connect_mongo()

Dgram.create(key = "c584e64745fa214d04a7699d0e1fed77ad4b490d", start_at = utc_now()).save()

disconnect_mongo()
