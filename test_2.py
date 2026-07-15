class Foo:

    def __init__(self, callback: callable):
        super().__init__()
        self.callback = callback

    def task(self):
        self.callback()


paths = ["path 1", "path 2", ]
app = "Photoshop"
data = (paths, app)
callback = lambda data=data: print(data)
foo = Foo(callback)
foo.task()