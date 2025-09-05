from cfg import Cfg


a = {
    i: getattr(Cfg, i)
    for i in vars(Cfg).keys()[2:10]
}

print(a)