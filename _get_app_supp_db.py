import shutil

from cfg import cnf

shutil.copyfile(src=cnf.db_file, dst="db.db")
