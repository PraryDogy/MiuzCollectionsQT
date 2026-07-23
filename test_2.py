from system.main_folder import Strings
all_slots_dicts = [
    {
        "mf_alias": "miuz",
        "mf_paths": [
            "/Volumes/shares/Studio/MIUZ/Photo/Art/Ready"
        ],
        "mf_stop_list": [
            "_Archive_Commerce_Брендинг",
            "Chosed",
            "LEVIEV"
        ],
        "mf_current_path": "/Volumes/shares/Studio/MIUZ/Photo/Art/Ready"
    },
    {
        "mf_alias": "panacea",
        "mf_paths": [
            "/Volumes/shares/Studio/PANACEA/Photo/Art/Ready"
        ],
        "mf_stop_list": [],
        "mf_current_path": 123
    }
]

for d in all_slots_dicts:
    base_types_ok = (
        isinstance(d[Strings.mf_alias], str),
        isinstance(d[Strings.mf_paths], list),
        isinstance(d[Strings.mf_stop_list], list),
        isinstance(d[Strings.mf_current_path], str)
    )
    if all(base_types_ok):
        lists_are_strings = (
            all(isinstance(i, str) for i in d[Strings.mf_paths]),
            all(isinstance(i, str) for i in d[Strings.mf_stop_list])
        )
        if all(lists_are_strings):
            print(f"Объект {d[Strings.mf_alias]} валиден!")
