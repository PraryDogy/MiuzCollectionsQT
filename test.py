from time import sleep
from threading import Thread


class Boo:
    def __init__(self, state: dict):
        self.state = state

    def run(self):
        for i in range(100):
            print(i)
            sleep(0.5)
            if not self.state:
                break
        print("finished")


class Foo:
    def __init__(self):
        self.state = {"can_scan": True}
        self.state = True

    def run(self):
        boo = Boo(self.state)
        t = Thread(target=boo.run)
        t.start()

        sleep(3)
        # self.state["can_scan"] = False
        self.state = False
        t.join()


foo = Foo()
foo.run()
