from utils.scaner import DubFinder

from database import Dbase
Dbase.create_engine()
dub_finder = DubFinder()
a = dub_finder.start()
print(a)