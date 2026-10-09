import py_compile
import traceback
try:
    py_compile.compile('dashboard.py', doraise=True)
    print('OK')
except Exception as e:
    traceback.print_exc()
    print('FAILED')
