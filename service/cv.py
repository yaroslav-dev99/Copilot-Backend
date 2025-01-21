from entity.live_interview import LiveInterview
from entity.prompt import cv_prompt
from util.logger import Logger
from util.llm import *

max_tokens = 2048

def process_cv(li: LiveInterview) -> None:
    if not li.cv:
        li.cv = ""
        li.experience = ""
        return

    try:
        messages = [
            { "role": "user", "content": cv_prompt["user"].format(cv = li.cv) },
            { "role": "assistant", "content": "{\n\t\"employment_history\": \"" }
        ]
        system_prompt = cv_prompt["system"]

        experience = call_openai_block(messages = messages, system_prompt = system_prompt, max_tokens = max_tokens, json_response = True, model = gpt_4_mini_model, tag = "cv")
    except Exception as exc:
        Logger.e(f"set_cv: {exc}")
        return

    li.experience = experience    
