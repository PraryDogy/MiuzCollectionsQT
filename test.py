from cfg import Cfg



a = [
    k for k in vars(Cfg)
    if not k.startswith("__")
    and
    not callable(getattr(Cfg, k))
]

# Cfg.write_json_data()

for i in a:
    print(i)