from cfg import JsonData
import os


JsonData.init()
JsonData.write_json_data()

class Test:
    @classmethod
    def smb_check(cls, brand_ind: int) -> bool:
        not_ok = False

        if not os.path.exists(JsonData.coll_folder):
            not_ok = True

        # elif JsonData.coll_folder in (JsonData.coll_folder_lst):
            # not_ok = True

        if not_ok:
            for brand in JsonData.coll_folder_lst[brand_ind]:

                for coll_folder in brand:
                    if os.path.exists(coll_folder):
                        JsonData.coll_folder = coll_folder
                        return True
                return False

        else:
            return True
        

print(*JsonData.coll_folder_lst)