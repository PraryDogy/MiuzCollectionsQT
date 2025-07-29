from cfg import JsonData

if JsonData.new_scaner:
    from .new_scaner.scaner_task import ScanerTask
    class ScanerTask(ScanerTask): ...
else:
    from .old_scaner.scaner_task import ScanerTask
    class ScanerTask(ScanerTask): ...