from system.utils import MainUtils
from datetime import datetime



now = datetime.now().replace(microsecond=0)
now = now.strftime("%Y-%m-%d %H-%M-%S") 

print(now)