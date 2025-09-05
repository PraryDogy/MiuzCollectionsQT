from cfg import Cfg

if Cfg.new_scaner:
    from .new_scaner.scaner_task import ScanerTask
    class ScanerTask(ScanerTask): ...
else:
    from .old_scaner.scaner_task import ScanerTask
    class ScanerTask(ScanerTask): ...