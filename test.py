from importlib.util import find_spec
import os
import sys
print(os.getcwd())
print(os.getenv('PYTHONPATH', 'no pythonpath'))
print(sys.path)
print(find_spec('numpy'))