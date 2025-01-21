from fastapi import APIRouter, Request
from entity.member import Member
from util.api import json_response
from util.logger import Logger
from entity.user import User
from service.account import *

router = APIRouter()

@router.api_route("/ms_webhook", methods = ["GET", "POST", "OPTIONS"])
async def ms_webhook(request: Request):
    data = await request.json()

    event = data.get("event")
    payload = data.get("payload", {})

    if event in ["member.created", "member.updated"]:
        member = Member(payload)
        user = User.get_by_ms_id(member.ms_id)
        
        if user is None:
            user = User.create(member.ms_id, member.email, member.name)
            Logger.i(f"new user registered: {member.ms_id}, {member.email}")
        else:
            user.verified = member.verified
            user.plan = member.plan
            
            Logger.e(f"user updated: {member.ms_id}, {member.email}")
        
        user.save()
    elif event in ["member.plan.added", "member.plan.canceled", "member.plan.updated"]:
        info = payload.get("member", {})
        ms_id = info.get("id")

        user = User.get_by_ms_id(ms_id)
        
        if user:
            if event == "member.plan.added" or event == "member.plan.updated":
                connection = payload.get("planConnection", {})
                plan_id = connection.get("planId")
                
                if plan_id in BusinessModel.plans.keys():
                    user.plan = BusinessModel.plans[plan_id]
                else:
                    user.plan = BusinessModel.Plan.Free
                    Logger.e(f"unknown plan id found: {plan_id}")                    
            elif event == "member.plan.canceled":
                user.plan = BusinessModel.Plan.Free

            user.verified = True
            user.save()

            Logger.i(f"user {user.email}'s plan updated with memberstack event: {event}")
        else:
            Logger.e(f"no user found with memberstack ID {ms_id} for {event}")

    return { "data": data }

@router.post("/user_inf")
async def query_user_info(request: Request):
    user = request.state.user
    info = get_user_info(user)

    response = json_response(200, 0, info)
    return response
