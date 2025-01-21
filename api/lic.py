from fastapi import APIRouter, Request, Response, BackgroundTasks
from util.api import json_response, request_to_json
from starlette.responses import StreamingResponse
from entity.live_interview import LiveInterview
from config import Config
from service.account import *
from service.lic import *
from util.misc import *

router = APIRouter()

@router.post("/trigger")
async def run_lic_trigger(request: Request, response: Response, bk_tasks: BackgroundTasks):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    if li_id is None: return json_response(200, -2, "Invalid live interview id.")

    chat = data.get("chat")
    if chat is None: return json_response(200, -3, "Invalid chat history.")
    
    url = data.get("url")
    if url is None: return json_response(200, -4, "Invalid url.")
    
    stream = data.get("stream")
    if stream is None: return json_response(200, -5, "Invalid stream.")
    
    urgent = data.get("urgent")
    if urgent is None: return json_response(200, -6, "Invalid urgent keyword.")
    
    is_auto = data.get("auto")
    if is_auto is None: return json_response(200, -7, "Invalid auto.")
    
    brief = data.get("brief")
    if brief is None: return json_response(200, -16, "Invalid brief.")

    question = data.get("question")
    if question is None: return json_response(200, -17, "Invalid question.")

    bullet = data.get("bullet", False)
    stamp = data.get("stamp", 0)

    user = request.state.user
    if user is None: return json_response(200, -8, "Invalid user.")
    
    li = LiveInterview.get_by_li_id(li_id)
    if li is None: return json_response(200, -9, "Live interview not found.")
    
    if li.ms_id != user.ms_id: return json_response(200, -10, "Live interview not match with user.")
    if not li.started: return json_response(200, -11, "Live interview not started.")

    if li.limit >= 0 and li.trigger >= li.limit: return json_response(200, -12, "Trigger limit is reached.")
    if is_auto and not li.autoable: return json_response(200, -13, "Auto hint is not available.")    
    
    if not is_same_meet_url(li.url, url):
        if url: # temporary for 2.0.3 bug
            return json_response(200, -14, "Url changed.")    
    
    if li.finished: return json_response(200, -15, "Live interview was finished.")

    chat_history = translate_to_chat_history(chat)
    urgent = urgent.strip()

    if stream:
        answer = lic_core_stream(chat_history, li, urgent, is_auto, brief, bullet, question, stamp, bk_tasks)
        return StreamingResponse(answer)
    else:
        answer = lic_core_block(chat_history, li, urgent, is_auto, brief, bullet, question, stamp, bk_tasks)
        return json_response(200, 0, answer)

@router.post("/query")
async def query_li(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    if li_id is None: return json_response(200, -2, "Invalid live interview id.")
    
    li = LiveInterview.get_by_li_id(li_id)
    if li is None: return json_response(200, -3, "Live interview not found.")
    
    response = json_response(200, 0, get_live_interview_info(li))    
    return response

@router.post("/start")
async def start_li(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    if li_id is None: return json_response(200, -2, "Invalid live interview id.")
    
    user = request.state.user
    li, code = start_live_interview(user, li_id)
    
    if code == -1: return json_response(200, -3, "Another interview was started.")
    if code == -2: return json_response(200, -4, "Too many interviews within a month.")
    if code == -3: return json_response(200, -5, "Live interview not found.")

    li.save()    
    response = json_response(200, 0, get_live_interview_info(li))

    return response

@router.post("/activate")
async def activate_li(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    if li_id is None: return json_response(200, -2, "Invalid live interview id.")
    
    url = data.get("url")
    if url is None or url == "": return json_response(200, -3, "Invalid url.")
    
    stt = data.get("stt", False)

    user = request.state.user
    li = activate_live_interview(user, li_id, url, stt)
    
    if li is None: return json_response(200, -4, "Live interview not found or URL changed.")
    if li.finished: return json_response(200, -5, "Live interview was finished.")
    if not li.started: return json_response(200, -6, "Live interview was not started.")

    response = json_response(200, 0, {})
    return response

@router.post("/cancel")
async def cancel_li(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    if li_id is None: return json_response(200, -2, "Invalid live interview id.")
    
    li = cancel_live_interview(li_id)
    
    if li is None: return json_response(200, -3, "Live interview not found.")
    if li.finished: return json_response(200, -4, "Live interview was finished.")
    if li.url: return json_response(200, -5, "Live interview was already activated.")

    response = json_response(200, 0, "OK")
    return response

@router.post("/remove")
async def remove_li(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    if li_id is None: return json_response(200, -2, "Invalid live interview id.")
    
    ok = remove_live_interview(li_id)
    if not ok: return json_response(200, -3, "Live interview not found.")
    
    response = json_response(200, 0, "OK")
    return response

@router.post("/transcript")
async def transcript_li(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    if li_id is None: return json_response(200, -2, "Invalid live interview id.")
    
    chat = data.get("chat")
    if chat is None: return json_response(200, -3, "Invalid transcription history.")

    text = translate_to_chat_history(chat)
    save_transcript(li_id, text)
    
    response = json_response(200, 0, "ok")
    return response

@router.post("/feedback")
async def feedback_li(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    if li_id is None: return json_response(200, -2, "Invalid live interview id.")
    
    li = LiveInterview.get_by_li_id(li_id)
    if li is None: return json_response(200, -3, "Live interview not found.")

    if li.feedback == "":
        li.feedback = get_feedback(li)
        li.save()
    
    response = json_response(200, 0, li.feedback)
    return response

@router.post("/finish")
async def finish_li(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    if li_id is None: return json_response(200, -2, "Invalid live interview id.")
    
    user_rate = data.get("user_rate")
    if user_rate is None: return json_response(200, -3, "Invalid user rate.")
    
    joba_rate = data.get("joba_rate")
    if joba_rate is None: return json_response(200, -4, "Invalid joba rate.")
    
    ok = finish_live_interview(li_id, user_rate, joba_rate)
    if not ok: return json_response(200, -4, "Live interview not found.")
    
    response = json_response(200, 0, "OK")
    return response

@router.post("/edit")
async def edit_li(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    li_id = data.get("li_id")
    scenario = data.get("scenario")
    company = data.get("company")
    position = data.get("position")
    lang = data.get("lang")
    start_at = data.get("start_at")
    keywords = data.get("keywords")
    cv = data.get("cv", "")
    jd = data.get("jd", "")
    instruct = data.get("instruct", "")

    start_at = s2time(start_at)
    
    if li_id is None:
        li = add_live_interview(
            request.state.user, scenario, company, position, lang, start_at, keywords, cv, instruct, jd
        )
    else:        
        li = update_live_interview(
            request.state.user, li_id, scenario, company, position, lang, start_at, keywords, cv, instruct, jd
        )
    
    if li is None: return json_response(200, -2, "Failed.")    
    response = json_response(200, 0, { "li_id": li.li_id })
    
    return response

@router.post("/all")
async def query_all_li(request: Request):
    user = request.state.user
    info = get_live_interviews(user)

    response = json_response(200, 0, info)
    return response

@router.get("/irably")
async def query_irably(request: Request):    
    response = json_response(200, 0, { 'msg': Config.IRABLY })
    return response
