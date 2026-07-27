class JsonData:
    __slots__ = ("app_ver", "lng_index", "theme", "scaner_minutes", "hide_digits_mf_lst")
    app_ver = 123
    lng_index = 0
    theme = 11111
    scaner_minutes = 20
    hide_digits_mf_lst = []

    @classmethod
    def get_data(cls):
        return {
            i: getattr(cls, i)
            for i in cls.__slots__
        }


print(JsonData.get_data())