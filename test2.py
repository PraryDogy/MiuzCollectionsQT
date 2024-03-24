import os
from time import sleep

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver


class Handler(PatternMatchingEventHandler):
    def __init__(self):

        dirs = [
            f"*/{i}/*"
            for i in ("001 Test_1", "002 Test_2")
            ]

        super().__init__(
            ignore_directories=True,
            ignore_patterns=dirs
            )

    def on_created(self, event: FileSystemEvent):
        print(event)

    def on_deleted(self, event: FileSystemEvent):
        print(event)


    def on_moved(self, event):
        print(event)


handler = Handler()
observer = PollingObserver()


observer.schedule(
    event_handler=handler,
    path="/Users/evlosh/Desktop/test",
    recursive=True,
    )
observer.start()

try:
    while True:
        sleep(20)
except KeyboardInterrupt:
    observer.stop()
observer.join()
    