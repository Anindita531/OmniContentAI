import traceback
from main import run_workflow

init = {'task': 'test', 'content': '', 'feedback': '', 'iterations': 0, 'is_compliant': False}

try:
    out = run_workflow(init)
    print(out)
except Exception:
    traceback.print_exc()
