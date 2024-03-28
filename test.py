import os
import traceback

from cfg import cnf


class Manager:
    flag = True

class FinderImages(dict):
    def __init__(self):
        super().__init__()
        self.run()

        try:
            self.run()

        except (OSError, FileNotFoundError):
            print(traceback.format_exc())
            Manager.flag = False

        if not self:
            print(111)

    def run(self):

        collections = [
            os.path.join(cnf.coll_folder, i)
            for i in os.listdir(cnf.coll_folder)
            if os.path.isdir(os.path.join(cnf.coll_folder, i))
            and i not in cnf.stop_colls
            ]

        if not collections:
            collections = [cnf.coll_folder]

        ln_colls = len(collections)
        step_value = 50 if ln_colls == 0 else 50 / ln_colls

        for collection_walk in collections:

            if not Manager.flag:
                return

            for root, _, files in os.walk(top=collection_walk):

                if not Manager.flag:
                    return

                for file in files:

                    print(file)

                    if not Manager.flag:
                        return
                    
                    # if not os.path.exists(cnf.coll_folder):
                    #     Manager.flag = False
                    #     return

                    pass


a = FinderImages()
print(a)