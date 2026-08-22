import os
from pathlib import Path
from cfg import Static


import os
from pathlib import Path
from typing import Optional

def get_rel_thumb_path(abs_thumb_path: str, app_data_dir = Static.APP_DATA_DIR):
    p_base = Path(app_data_dir.strip(os.sep))
    p_abs = Path(abs_thumb_path.strip(os.sep))
    if p_abs.is_relative_to(p_base):
        return os.sep + str(p_abs.relative_to(p_base))




rel_thumb_path = "/Users/evlosh/Library/Application Support/Collections/hashdir/Мамия-38/38b5878a5b560086d23ba49451ed61c4.jpg"


result = get_rel_thumb_path(rel_thumb_path)
print(result)