from cfg import cnf

dirs = [
            f"*/{i}/*"
            for i in cnf.stop_colls
            ]
import os
dirs = [
    os.path.join(cnf.coll_folder, i)
    for i in cnf.stop_colls
]



print(dirs)