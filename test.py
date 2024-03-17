# from watchdog.events import FileSystemEvent, FileSystemEventHandler, LoggingEventHandler
# from watchdog.observers.polling import PollingObserver
# from watchdog.observers import Observer
# from time import sleep

# class Handler(FileSystemEventHandler):
#     def on_any_event(self, event) -> None:
#         print(f"{event.event_type}: {event.src_path}")
#         return super().on_any_event(event)
    

# handler = Handler()
# observer = PollingObserver()
# flag = True

# observer.schedule(
#     event_handler=handler,
#     path="/Volumes/Untitled/_Collections",
#     recursive=True
#     )
# observer.start()

# try:
#     while flag:
#         sleep(1)
# except KeyboardInterrupt:
#     observer.stop()
#     observer.join()

a = None
b = None
c = 1


if not any((a, b, c)):
    print(1)