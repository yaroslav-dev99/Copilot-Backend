from entity.prompt import auto_check_prompt, trigger_prompt, feedback_prompt, dictionary
from entity.live_interview import LiveInterview
from entity.trigger_record import TriggerRecord
from fastapi import BackgroundTasks
from util.misc import utc_now, t2str
from util.logger import Logger
from util.llm import *
from config import Config
import json

max_tokens = 2048
separator = Config.HINT_SEPARATOR

def lic_core_block(chat_history: str, li: LiveInterview, urgent_keyword: str, is_auto: bool, brief: bool, bullet: bool, question: str, stamp: int, bk_tasks: BackgroundTasks = None):
    if is_auto:
        if not check_auto_trigger(chat_history, li, stamp)[0]: return separator
        
        li.is_auto_processing = True
        li.last_stamp = stamp
        li.save()

    try:
        messages, system_prompt = get_trigger_messages(chat_history, li, urgent_keyword, brief, bullet, question)    
        answer = call_openai_block(messages = messages, system_prompt = system_prompt, max_tokens = max_tokens, json_response = True, model = gpt_4_mini_model, tag = "trigger")
        
        answer = json.loads(answer)
        text = answer["topic"] + separator + answer["response"]

        if is_auto:
            li.is_auto_processing = False
            li.save()

        if bk_tasks: bk_tasks.add_task(on_trigger_done, li, chat_history, text, urgent_keyword, gpt_4_mini_model, is_auto)
        return text
    except Exception as exc:
        Logger.e(f"lic_core_block: {exc}")

        if is_auto:
            li.is_auto_processing = False
            li.save()

        return f"Error{separator}Awfully sorry for inconvenience."

def lic_core_stream(chat_history: str, li: LiveInterview, urgent_keyword: str, is_auto: bool, brief: bool, bullet: bool, question: str, stamp: int, bk_tasks: BackgroundTasks = None):
    if is_auto:
        if not check_auto_trigger(chat_history, li, stamp)[0]:
            yield separator
            return
        
        li.is_auto_processing = True
        li.last_stamp = stamp
        li.save()

    try:
        messages, system_prompt = get_trigger_messages(chat_history, li, urgent_keyword, brief, bullet, question)
        answer = call_openai_stream(messages = messages, system_prompt = system_prompt, max_tokens = max_tokens, json_response = True, model = gpt_4_mini_model, tag = "trigger")
        
        quotes, text, prev_ch = 0, "", ""
        
        for chunk in answer:
            out_chunk = ""
            
            for ch in chunk:
                is_quote = (ch == '"' and prev_ch != "\\")
                prev_ch = ch
                
                if is_quote: quotes += 1
                
                if quotes == 3:
                    if not is_quote: out_chunk += ch
                elif quotes == 7:
                    if is_quote:
                        out_chunk += separator
                    else:
                        out_chunk += ch
            
            if out_chunk:
                yield out_chunk
                text += out_chunk

        if is_auto:
            li.is_auto_processing = False
            li.save()

        if bk_tasks:
            bk_tasks.add_task(on_trigger_done, li, chat_history, text, urgent_keyword, gpt_4_mini_model, is_auto)
    except Exception as exc:
        Logger.e(f"lic_core_stream: {exc}")

        yield f"Error{separator}Awfully sorry for inconvenience."

        if is_auto:
            li.is_auto_processing = False
            li.save()

def lic_core_stream_test(chat_history: str, li: LiveInterview, urgent_keyword: str, brief: bool, bullet: bool, question: str):
    _, auto_report = check_auto_trigger(chat_history, li)
    auto_report = json.dumps(auto_report) + "\n"
    
    messages, system_prompt = get_trigger_messages(chat_history, li, urgent_keyword, brief, bullet, question)
    answer = call_openai_stream(messages = messages, system_prompt = system_prompt, max_tokens = max_tokens, json_response = True, model = gpt_4_mini_model, tag = "trigger")
    
    yield auto_report

    for chunk in answer:
        yield chunk

def check_auto_trigger(chat_history: str, li: LiveInterview, stamp: int)-> tuple:
    if li.is_auto_processing: return False, {"a": False, "b": False}
    if stamp <= li.last_stamp and stamp > 0: return False, {"a": False, "b": False}

    user_prompt = auto_check_prompt["user"].format(
        scenario = dictionary["scenario"][li.scenario],
        position = li.position,
        company = li.company,
        keywords = ", ".join(li.keywords),
        log = chat_history
    )
    sys_prompt = auto_check_prompt["system"].format(
        last_hint = li.last_hint
    )

    messages = [
        { "role": "user", "content": user_prompt }
    ]
    answer = None

    try:
        answer = call_openai_block(messages = messages, system_prompt = sys_prompt, max_tokens = 40, json_response = True, model = gpt_4_model, tag = "vad")
        answer = json.loads(answer.lower())
        
        ok = (not is_true(answer["a"])) and is_true(answer["b"])

        if not ok: Logger.d("check_json: " + str(answer))
        return ok, answer
    except Exception as exc:
        Logger.e(f"check_auto_trigger: {exc}")

        return True, {"a": False, "b": False}

def is_true(v):
    if v == True: return True
    if v == False: return False
    
    if type(v) == str and ("t" in v or "y" in v): return True
    return False

def get_trigger_messages(chat_history: str, li: LiveInterview, urgent_keyword: str, brief: bool, bullet: bool, question: str) -> list:
    keywords = list(set(li.keywords + li.jargons))

    user_prompt = trigger_prompt["user"].format(
        scenario = dictionary["scenario"][li.scenario],
        position = li.position,
        company = li.company,
        keywords = ", ".join(keywords),
        urgent = trigger_prompt["urgent"].format(keyword = urgent_keyword) if urgent_keyword else "",
        topic = trigger_prompt["topic"].format(question = question) if question else "",
        log = chat_history
    )    
    sys_prompt = trigger_prompt["system"].format(
        experience = trigger_prompt["experience"].format(experience = li.experience) if li.experience else "",
        instruct = f"\n{li.instruct}\n" if li.instruct else "",
        brief = trigger_prompt["brief"] if brief else "",
        bullet = dictionary["bullet"][bullet],
        lang = li.lang.name
    )
    messages = [
        { "role": "user", "content": user_prompt }
    ]
    return messages, sys_prompt

def translate_to_chat_history(json_history):
    chat_history = ""
    prev_speaker = None
    
    for h in json_history:
        if h["speaker"] == prev_speaker:
            chat_history += " " + h["talk"].replace("\n", " ")
        else:
            speaker = h["speaker"]
            if speaker.lower() == "you": speaker = "me"

            chat_history += "\n" + speaker + ": " + h["talk"].replace("\n", " ")
        
        prev_speaker = h["speaker"]

    return chat_history

def on_trigger_done(li: LiveInterview, chat: str, answer: str, urgent_keyword: str, model: str, is_auto: bool):
    if urgent_keyword != "" and urgent_keyword not in li.keywords:
        li.jargons.append(urgent_keyword)
    
    if li.trigger == 0: li.first_trigger_at = utc_now()

    li.trigger += 1
    li.last_hint = answer
    li.save()

    TriggerRecord.create(
        ms_id = li.ms_id,
        li_id = li.li_id,
        chat = chat,
        answer = answer,
        model = model,
        is_auto = is_auto
    ).save()

def is_same_meet_url(url1, url2):
    if url1 == url2: return True
    if "teams.live.com" in url1 and "teams.live.com" in url2: return True

    return False

def get_feedback(li: LiveInterview) -> dict:
    keywords = list(set(li.keywords + li.jargons))

    user_prompt = feedback_prompt["user"].format(
        scenario = dictionary["scenario"][li.scenario],
        position = li.position,
        company = li.company,
        keywords = ", ".join(keywords),
        log = li.transcript
    )
    messages = [
        { "role": "user", "content": user_prompt }
    ]

    answer = call_openai_block(messages = messages, system_prompt = feedback_prompt["system"], max_tokens = 4096, json_response = True, model = gpt_4_mini_model, tag = "feedback")
    answer = json.loads(answer)

    feedback = f"Time: {t2str(li.start_at)}\nStage: {li.scenario.name} Interview\nTitle: {li.position}\nCompany: {li.company}\n\n"
    feedback += f"* Your overall performance was {stringfy_score(answer['overall_score'])}.\n\n"
    feedback += answer["feedback"]
    feedback += "\n\n"

    for step in answer["steps"]:
        feedback += f"[Question]: {step['q']}\n"
        feedback += f"[Answer]: {step['a']}\n"
        feedback += f"[Evaluation]: {stringfy_score(step['score'])}\n\n"
    
    return feedback

def stringfy_score(score):
    if score <= 0:
        return "`WORST`"
    elif score == 1:
        return "`NOT GOOD`"
    elif score == 2:
        return "`GOOD`"
    else:
        return "`PERFECT`"
