from fastapi import APIRouter, Request
from util.api import json_response, request_to_json
from config import Config
import random
import copy

router = APIRouter()

PRE_FILLERS = [
    "", "", "", "", "", "",
    "Ok, ", "Good, ", "Perfect, ", "Got it, ", "Ok perfect, ", "Very good, ", "Cool, ", "Awesome, ", "Ok ok, ", "Nice, ", "Well, ", "Now the next question is, "
]

@router.post("/info")
async def get_demo_info(request: Request):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, "Invalid request params.")

    demo_id = data.get("demo_id")
    if demo_id is None: return json_response(200, -2, "Invalid demo id.")

    info = copy.deepcopy(Config.DEMO[str(demo_id)])
    user = request.state.user

    for i, q in enumerate(info["question"]):
        info["question"][i] = random.sample(PRE_FILLERS, 1)[0] + q
    
    info["question"].insert(
        0,
        f"Hello {user.name}, my name is Silvia Morata, the HR manager at {info['company']}. Thank you for applying for this position. Now I'd like to ask you a few questions. Are you ready?"
    )
    info["question"].append(
        "Perfect. Well, your experience seems relevant to what we are looking for. Our HR team will review this interview progress carefully, and let you know the result through email. Very nice talking to you."
    )
    info["question"].append(
        "OK, good bye."
    )
    response = json_response(200, 0, info)
    return response
