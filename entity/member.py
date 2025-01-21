from entity.business_model import BusinessModel
from util.logger import Logger
from util.misc import utc_now
from config import Config

class Member():
    promo = {
        "promo_0": BusinessModel.Plan.Free,
        "promo_1": BusinessModel.Plan.Premium,
        "promo_2": BusinessModel.Plan.Unlimited
    }
    
    def __init__(self, data):
        plans = data.get("planConnections", [])
        
        self.ms_id = data.get("id", "")
        self.email = data.get("auth", {}).get("email", "")
        self.name = data.get("customFields", {}).get("name", "")
        self.verified = data.get("verified", False)
        
        self.plan = BusinessModel.Plan.Free
        self.is_admin = False
        
        for p in plans:
            if p.get("active", False) and p.get("planId"):
                plan = BusinessModel.plans.get(p.get("planId"), BusinessModel.Plan.Free)

                if plan == BusinessModel.Plan.Premium or plan == BusinessModel.Plan.Unlimited:
                    if plan.value > self.plan.value: self.plan = plan
                elif p.get("planId") == Config.ADMIN_PLAN:
                    self.is_admin = True

        now_str = utc_now().strftime("%Y-%m-%d %H:%M:%S")
        meta = data.get("metaData", {})
        
        for pk, expire_at in meta.items():
            plan = Member.promo.get(pk, BusinessModel.Plan.Free)
            
            if now_str < expire_at and self.plan.value < plan.value:
                self.plan = plan
                Logger.d(f"{pk} detected for {self.email}/{self.ms_id}")
