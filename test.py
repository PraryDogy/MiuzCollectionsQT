from multiprocessing import Process, Queue

from system.main_folder import Mf
from system.scaner import AllDirScaner

def main():
    Mf.init()
    q = Queue()
    # AllDirScaner.start(Mf.list_, q)
    process = Process(
        target=AllDirScaner.start,
        args=(Mf.list_, q)
    )

    process.start()
    process.join()


if __name__ == "__main__":
    main()