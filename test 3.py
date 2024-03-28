import os
from cfg import cnf

def migrate_coll(old_coll: str, new_coll: str):
    from database import Dbase, ThumbsMd
    import sqlalchemy

    q = sqlalchemy.select(ThumbsMd.id, ThumbsMd.src)
    sess = Dbase.get_session()
    res = sess.execute(q).fetchall()

    new_res = [
        (res_id, src.replace(old_coll, new_coll))
        for res_id, src in res
        ]
    
    for res_id, src in new_res:
        q = sqlalchemy.update(ThumbsMd).values({"src": src}).filter(ThumbsMd.id==res_id)
        sess.execute(q)

    sess.commit()
    sess.close()
    cnf.coll_folder = new_coll


def smb_check():
    if not os.path.exists(cnf.coll_folder):
        cut_path = cnf.coll_folder.strip("/").split("/")[2:]

        assumed_dirs = [
            os.path.join("/Volumes", i, *cut_path)
            for i in os.listdir("/Volumes")
            ]
        
        for i in assumed_dirs:
            if os.path.exists(i):
                migrate_coll(cnf.coll_folder, i)
                break

        return False
    
    else:
        return True
