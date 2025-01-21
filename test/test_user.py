import os
os.sys.path.append(os.getcwd())

from main import initialize, finalize
from entity.user import User

initialize("dev")

user = User.create("2150001", "12345@gmail.com")
print(user.user_id)
user.save()

print(user.to_json())

saved_user = User.objects(user_id = user.user_id).first()
print(saved_user.to_json())

finalize()
