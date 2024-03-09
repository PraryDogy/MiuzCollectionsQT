try:
    from .rus import Rus
    from. eng import Eng
except Exception:
    pass

from .main import LangAdmin
from .create_files import create_all_files