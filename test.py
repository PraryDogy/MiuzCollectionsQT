src = "/Volumes/Shares/Collections/6 Arabella"


import time

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers.polling import PollingObserver


class Handler(FileSystemEventHandler):
    def on_any_event(self, event: FileSystemEvent) -> None:
        print(event.src_path)
        return super().on_any_event(event)
    

observer = PollingObserver()
handler = Handler()

observer.schedule(event_handler=handler, path=src, recursive=True)
observer.start()

try:
    while True:
        time.sleep(3)
finally:
    observer.stop()
    observer.join()