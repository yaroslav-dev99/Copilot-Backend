from entity.live_interview import LiveInterview
from entity.prompt import jd_prompt
from util.logger import Logger
from util.llm import *
import json

max_tokens = 2048

def process_jd(li: LiveInterview) -> None:
    if not li.jd:
        li.jd = ""
        li.jargons = []
        return

    try:
        messages = [
            { "role": "user", "content": jd_prompt["user"].format(jd = li.jd) },
            { "role": "assistant", "content": "{\n\t\"result\": \"" }
        ]
        system_prompt = jd_prompt["system"]

        js = call_openai_block(messages = messages, system_prompt = system_prompt, max_tokens = max_tokens, json_response = True, model = gpt_4_mini_model, tag = "jd")
        js = json.loads(js)
    except Exception as exc:
        Logger.e(f"set_jd analysis: {exc}")
        return

    try:
        if li.position == "": li.position = js.get("position", "")
        if li.company == "": li.company = js.get("company", "")
        
        li.jargons = js.get("words", []) or []

        if len(li.keywords) == 0: li.keywords = li.jargons
    except Exception as exc:
        Logger.e(f"set_jd save: {exc}")
