class Filter:
    list_: list["Filter"] = []
    __slots__ = ["names", "real", "value", "system"]

    def __init__(self, names: list, real: str, value: bool, system: bool):
        """
        Создаёт фильтр.

        Аргументы:
        names (list[str]): Названия фильтра (например, на русском и английском).
        real (str | None): Имя папки, к которой относится фильтр. None — для системных фильтров.
        value (bool): Активен ли фильтр.
        system (bool): Системный фильтр. 
        Если True — из бд загружаются записи, не подходящие под обычные фильтры.
        Пример: system=True → загружаются записи, не относящиеся к "Продукт" и "Модели".
        """
        self.names = names
        self.real = real
        self.value = value
        self.system = system
        Filter.list_.append(self)


Filter(["Продукт", "Product"], "1 IMG", False, False)
Filter(["Модели", "Model"], "2 MODEL IMG", False, False)
Filter(["Остальное", "Other"], None, False, True)
