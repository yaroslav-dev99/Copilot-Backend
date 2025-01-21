import os
os.sys.path.append(os.getcwd())

from util.mongo import *
connect_mongo()

from entity.live_interview import LiveInterview
from entity.language import Language
from util.misc import utc_now
from service.lic import *
import time

chat_history = """
    interviewer-> so let's dive in two the next phase of our interview it'll be a short technical questions okay?
    you-> yes sir please i am ready
    interviewer-> good the first, what is the we book in react to jaiss? can you tell me what we book functions you know and what experience do yo have?
    you-> yes, sure. err
    interviewer-> hmm?
    you-> way books in React.js are a powerful feature that allows developers to build reusable logic. I have experience implementing way books for real time data fetching and handling asynchronous operations efficiently. One specific example is using web hooks to trigger updates in the UI when new data is available without the need for manual refresh. This not only enhances user experience but also improves the overall performance of the application.
    interviewer-> cool so what is the name of the function you mentioned?
    you-> oh, well... er...
    interviewer-> okay, that's fine. well, now i am gonna introduce our project
"""
tick = time.time()

li = LiveInterview.create(
    "", LiveInterview.Scenario.Tech, "", "Senior Fullstack Developer", utc_now(),
    ["React", "Javascript", "Frontend", "SQL", "Database", "ETL"], Language.English, ""
)
answer = lic_core_stream_test(chat_history = chat_history, li = li, urgent_keyword = "", brief = True, bullet = True, question = "")
full = ""

for chunk in answer:
    if full == "" and len(chunk) > 0:
        dur = time.time() - tick
        print("result in {:.3f}secs".format(dur))

    full += chunk

dur = time.time() - tick

print("result in {:.3f}secs".format(dur))
print("answer->", full)

disconnect_mongo()
