from config import Config
import openai

gpt_35_model = "gpt-3.5-turbo-0125"
gpt_4_model = "gpt-4o"
gpt_4_mini_model = "gpt-4o-mini"

max_tokens = 2048
retry_limit = 5

def call_openai_block(messages, system_prompt = "", model = gpt_4_model, temperature = 0, max_tokens = max_tokens, json_response = False, tag = ""):
    client = openai.OpenAI(api_key = Config.OPENAI_KEY, max_retries = retry_limit)
    
    params = {
        "model": model,
        "messages": messages + ([{ "role": "system", "content": system_prompt }] if system_prompt != "" else []),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
        "user": f"{Config.PROJECT_ID}/{'prod' if Config.IS_PRODUCT else 'test'}/{tag}"
    }
    if json_response: params["response_format"] = { "type": "json_object" }
    
    completion = client.chat.completions.create(**params)
    response = completion.choices[0].message.content    
    client.close()
    
    return response

def call_openai_stream(messages, system_prompt = "", model = gpt_4_model, temperature = 0, max_tokens = max_tokens, json_response = False, tag = ""):
    client = openai.OpenAI(api_key = Config.OPENAI_KEY, max_retries = retry_limit)
    
    params = {
        "model": model,
        "messages": messages + ([{ "role": "system", "content": system_prompt }] if system_prompt != "" else []),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
        "user": f"{Config.PROJECT_ID}/{'prod' if Config.IS_PRODUCT else 'test'}/{tag}"
    }
    if json_response: params["response_format"] = { "type": "json_object" }
    
    completion = client.chat.completions.create(**params)
        
    for chunk in completion:
        delta = chunk.choices[0].delta.content or ""
        yield delta
    
    client.close()
