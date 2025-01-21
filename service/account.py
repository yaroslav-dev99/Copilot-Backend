from entity.live_interview import LiveInterview
from entity.business_model import BusinessModel
from entity.ospace import Ospace
from entity.dgram import Dgram
from entity.user import User
from datetime import datetime, timedelta
from service.lic import *
from service.cv import *
from service.jd import *
from util.misc import *

def get_user_info(user: User) -> dict:
    info = {
        "ms_id": user.ms_id,
        "email": user.email,
        "name": user.name,
        "verified": user.verified,
        "li": get_live_interviews(user),
        "plan_desc": BusinessModel.get_plan_desc(user.plan),
        "stt_desc": BusinessModel.get_stt_desc(),
        "auto_count": BusinessModel.auto_count
    }
    return info

def start_live_interview(user: User, li_id: int):    
    now_str, month = t2str(utc_now()), timedelta(days = 30)
    cur_li, recent_count = None, 0
    
    for li in LiveInterview.objects(ms_id = user.ms_id):
        if not li.finished:
            if li.li_id == li_id:
                cur_li = li
            elif li.started:
                return None, -1
        else:
            if t2str(li.first_trigger_at + month) > now_str: recent_count += 1

    if BusinessModel.monthly_limits[user.plan] > 0 and recent_count >= BusinessModel.monthly_limits[user.plan]:
        return None, -2
    
    if cur_li:
        cur_li.limit = BusinessModel.lic_limits[user.plan]
        cur_li.autoable = BusinessModel.auto_hints[user.plan]
        cur_li.stt = BusinessModel.stt[user.plan]
        cur_li.detail = BusinessModel.detail[user.plan]
        cur_li.started = True

        return cur_li, 0
    else:
        return None, -3

def cancel_live_interview(li_id: int):
    li = LiveInterview.get_by_li_id(li_id)
    
    if li:
        if not li.finished and li.url == "":
            li.started = False
            li.save()
    
    return li

def activate_live_interview(user: User, li_id: int, url: str, stt: bool):
    li = LiveInterview.get_by_li_id(li_id)
    
    if li:
        if li.url and not is_same_meet_url(li.url, url) : return None

        if not li.finished and li.started:
            trigger = li.trigger
            
            if "teams.live.com" not in url and Config.DEMO_SEG not in url:
                li_list = LiveInterview.objects(ms_id = user.ms_id)
                
                for oli in li_list:
                    if oli.url == url and oli.trigger > trigger: trigger = oli.trigger

            li.url = url
            li.trigger = trigger
            li.dg_key = Dgram.get_key()
            li.ocr_key = Ospace.get_key()
            li.is_cc = not stt
            li.is_auto_processing = False
            li.last_stamp = 0
            li.save()

    return li

def save_transcript(li_id: int, text: str):
    li = LiveInterview.get_by_li_id(li_id)
    
    if li:
        li.transcript += text
        li.save()        
    else:
        return None

def finish_live_interview(li_id: int, user_rate: int, joba_rate: int) -> bool:
    li = LiveInterview.get_by_li_id(li_id)
    
    if li:
        li.started = False
        li.finished = True
        li.user_rate = user_rate
        li.joba_rate = joba_rate
        li.save()
        return True
    else:
        return False
    
def remove_live_interview(li_id: int) -> bool:
    li = LiveInterview.get_by_li_id(li_id)
    
    if li:
        li.delete()
        return True
    else:
        return False

def get_live_interviews(user: User) -> list:
    li_list = []
    
    for li in LiveInterview.objects.filter(ms_id = user.ms_id, finished = False).order_by("start_at"):
        info = get_live_interview_info(li)
        li_list.append(info)
    
    return li_list

def get_live_interview_info(li: LiveInterview):
    return {
        "li_id": li.li_id,
        "url": li.url,
        "scenario": li.scenario,
        "company": li.company,
        "position": li.position,
        "lang": li.lang,
        "start_at": t2str(li.start_at),
        "keywords": [k for k in li.keywords],
        "started": li.started,
        "trigger": li.trigger,
        "limit": li.limit,
        "autoable": li.autoable,
        "stt": li.stt,
        "detail": li.detail,
        "dg_key": li.dg_key,
        "dg_model": "nova-2",
        "ocr_key": li.ocr_key,
        "cv": li.cv,
        "jd": li.jd
    }

def add_live_interview(user: User, scenario: LiveInterview.Scenario, company: str, position: str, lang: int, start_at: datetime, keywords: list, cv: str, instruct: str, jd: str) -> LiveInterview:
    li = LiveInterview.create(
        ms_id = user.ms_id,
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
    if li:
        if BusinessModel.cv[user.plan]: process_cv(li)
        if BusinessModel.jd[user.plan]: process_jd(li)
        
        li.save()
    
    return li

def update_live_interview(user: User, li_id: int, scenario: LiveInterview.Scenario, company: str, position: str, lang: int, start_at: datetime, keywords: list, cv: str, instruct: str, jd: str) -> LiveInterview:
    li = LiveInterview.get_by_li_id(li_id)

    if li:
        if li.finished: return None

        li.scenario = scenario
        li.company = company
        li.position = position
        li.start_at = start_at
        li.keywords = keywords
        li.lang = lang
        li.instruct = instruct

        if li.cv != cv:
            li.cv = cv
            if BusinessModel.cv[user.plan]: process_cv(li)

        if li.jd != jd:
            li.jd = jd
            if BusinessModel.jd[user.plan]: process_jd(li)

        li.save()        
        return li
    
    return None
