class Slots:
    name = "name"
    paths = "paths"
    stop_list = "stop_list"
    _curr_path = "_curr_path"

class MainFolder:
    current: "MainFolder" = None
    list_: list["MainFolder"] = []
    __slots__ = [Slots.name, Slots.paths, Slots.stop_list, Slots._curr_path]


    def __init__(self, name: str, paths: list[str], stop_list: list[str]):

        super().__init__()
        self.name = name
        self.paths = paths
        self.stop_list = stop_list
        self._curr_path: str = None # этот аттрибут нужен для сканера

    # def get_data(self):
    #     return [self.name, self.paths, self.stop_list]
    
    def get_data(self):
        return [getattr(self, i) for i in MainFolder.__slots__]


a = MainFolder("test", ["path", "path"], ["stop", "stop"])
print(a.get_data())