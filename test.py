import traceback
import os

class Utils:
    @staticmethod
    def print_err(parent: object, error: Exception):
        # Получаем текущий стек вызовов
        tb = traceback.extract_tb(error.__traceback__)
        last_call = tb[-1]
        filepath = last_call.filename
        filename = os.path.basename(filepath)
        class_name = parent.__class__.__name__
        line_number = last_call.lineno
        error_message = str(error)
        
        print()
        print(f"{filename} > {class_name} > row {line_number}: {error_message}")
        print(f"{filepath}:{line_number}")
        print()

class Foo:
    def __init__(self):
        super().__init__()
        self.test = []

    def test_method(self):
        try:
            self.test[1]
        except Exception as e:
            Utils.print_err(self, e)


a = Foo()
a.test_method()

