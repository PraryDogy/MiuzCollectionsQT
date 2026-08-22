import os


def remove_mf_path():
    mf_path = "/root/volumes"
    abs_path = "/root/volumes/test/adfsd/dsfsdf"


from pathlib import Path

def remove_mf_path(mf_path: str, abs_path: str) -> str:
    mf_path = os.path.join(os.sep, mf_path.strip(os.sep))
    abs_path = os.path.join(os.sep, abs_path.strip(os.sep))
    return os.path.join(os.sep, abs_path.removeprefix(mf_path))



import os
from pathlib import Path


def add_mf_path(mf_path: str, rel_path: str) -> str:
    p_mf = Path(mf_path.strip(os.sep))
    p_abs = Path(rel_path.strip(os.sep))
    if p_abs.is_relative_to(p_mf):
        return os.sep + str(p_abs)
    combined_path = p_mf / p_abs
    return os.sep + str(combined_path)





mf_path = "root/volumes/"
abs_path = "/test/adfsd/dsfsdf/1.jpg"
result = add_mf_path(mf_path, abs_path)

print(result)