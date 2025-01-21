from config import Config
from typing import Dict
from enum import Enum

class BusinessModel():
    class Plan(Enum):
        Free = 0
        Premium = 1
        Unlimited = 2

    plans = {
        Config.FREE_PLAN: Plan.Free,
        Config.PREMIUM_PLAN: Plan.Premium,
        Config.UNLIMITED_PLAN: Plan.Unlimited
    }
    lic_limits = {
        Plan.Free: 3,
        Plan.Premium: -1,
        Plan.Unlimited: -1
    }
    auto_hints = {
        Plan.Free: False,
        Plan.Premium: True,
        Plan.Unlimited: True
    }
    stt = {
        Plan.Free: True,
        Plan.Premium: True,
        Plan.Unlimited: True
    }
    detail = {
        Plan.Free: False,
        Plan.Premium: True,
        Plan.Unlimited: True
    }
    cv = {
        Plan.Free: False,
        Plan.Premium: True,
        Plan.Unlimited: True
    }
    jd = {
        Plan.Free: False,
        Plan.Premium: True,
        Plan.Unlimited: True
    }
    monthly_limits = {
        Plan.Free: 10,
        Plan.Premium: 60,
        Plan.Unlimited: -1
    }

    auto_count = True

    @staticmethod
    def get_plan_desc(plan: Plan) -> Dict[str, str]:
        if plan == BusinessModel.Plan.Free:
            return {
                "title": "Free Plan",
                "desc": "3 triggers per interview",
                "upgrade": True
            }
        elif plan == BusinessModel.Plan.Premium:
            return {
                "title": "Premium Plan",
                "desc": "Unlimited triggers",
                "upgrade": True if Config.PROJECT_ID == "ntro" else False
            }
        elif plan == BusinessModel.Plan.Unlimited:
            return {
                "title": "Diamond Plan" if Config.PROJECT_ID == "ntro" else "Unlimited Plan",
                "desc": "Unlimited triggers",
                "upgrade": False
            }
        else:
            return BusinessModel.get_plan_desc(BusinessModel.Plan.Free)

    @staticmethod
    def get_stt_desc() -> str:
        return ""
