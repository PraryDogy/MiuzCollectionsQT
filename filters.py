class Filter:
    filters_list: list["Filter"] = []
    __slots__ = ["names", "real", "value", "system"]

    def __init__(self, names: list, real: str, value: bool, system: bool):
        self.names = names
        self.real = real
        self.value = value
        self.system = system
        Filter.filters_list.append(self)


Filter(
    names=["Продукт", "Product"],
    real="1 IMG",
    value=False,
    system=False
)

Filter(
    names=["Модели", "Model"],
    real="2 MODEL IMG", 
    value=False, 
    system=False
)

Filter(
    names=["Остальное", "Other"], 
    real=None, 
    value=False, 
    system=True
)
