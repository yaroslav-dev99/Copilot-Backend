from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from entity.user import User
from service.account import *
from util.memberstack import *
from util.logger import Logger
from fastapi import Request
from config import Config
import time

class MSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        printable, client_ip = False, None
        tick = time.time()

        if request.method.lower() != "get" and not request.url.path.endswith("/account/ms_webhook"):
            printable = True
            
            x_forwarded_for = request.headers.get("x-forwarded-for")           
        
            if x_forwarded_for:
                client_ip = x_forwarded_for.split(",")[0]
            else:
                client_ip = request.client.host
            
            ms_token = request.headers.get("Authorization")
            user = None
            
            if ms_token is None:
                ms_token = request.query_params.get("ms_token")
            elif ms_token.startswith("Bearer "):
                ms_token = ms_token[7:]

            ms_id = request.query_params.get("ms_id")

            is_unsafe_request = request.url.path.endswith("/lic/trigger")
            is_admin_request = "/admin/" in request.url.path

            if (is_unsafe_request or Config.NO_MS_TOKEN) and ms_id: user = User.get_by_ms_id(ms_id)
            
            if ms_token and ((user is None) or (not user.verified) or (is_admin_request and not user.is_admin)):
                ms_id = get_ms_id_by_token(ms_token)            
                if ms_id is None: return JSONResponse(json_response(403, -1, "Failed to verify MS Token."))
                
                member = get_member_by_ms_id(ms_id)
                
                if member is None: return JSONResponse(json_response(403, -2, "Not found Memberstack user."))
                if user is None: user = User.get_by_ms_id(ms_id)
                
                if user is None:
                    user = User.create(ms_id, member.email, member.name)
                    
                    if user is None:
                        return JSONResponse(json_response(403, -3, f"Failed to create unexpected user: {ms_id}, {member.email}"))
                    else:
                        Logger.w(f"unexpected user created: {ms_id}, {member.email}")
                
                user.plan = member.plan
                user.verified = member.verified
                user.is_admin = member.is_admin
                user.ip = client_ip
                user.save()

            if user is None: return JSONResponse(json_response(403, -4, "Failed to get user from request."))
            if not user.verified: return JSONResponse(json_response(403, -5, "Unverified account."))
            
            if user.status == User.Status.Suspended: return JSONResponse(json_response(403, -6, "Suspended account."))
            if user.status == User.Status.Closed: return JSONResponse(json_response(403, -7, "Closed account."))            
            if is_admin_request and not user.is_admin: return JSONResponse(json_response(403, -8, "Not admin account."))

            Logger.d("user: {}, memberstack delay = {:.2}s".format(user.email, time.time() - tick))
            tick = time.time()

            request.state.user = user

        response = await call_next(request)        
        
        if printable:
            Logger.d("api delay = {:.2}s".format(time.time() - tick))
            Logger.d(f"{client_ip} - \"{request.method} {request.url.path}\" {response.status_code}")
        
        return response

async def request_to_json(request):
    try:
        data = await request.json()
        return data
    except Exception as exception:
        Logger.e(f"req2json failed. {exception}")
        return None

def json_response(status: int, code : int, msg : str):
    return {"status": status, "code": code, "msg": msg}
