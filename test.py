from system.main_folder import Mf
from system.scaner import AllDirScaner
from multiprocessing import Queue

Mf.init()
q = Queue
AllDirScaner.start(Mf.list_, q)