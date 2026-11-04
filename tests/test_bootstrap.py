"""Regressions for stale modules in a long-running Streamlit process."""
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeploymentImports(unittest.TestCase):
    def test_stale_solver_and_foreign_plot_module_are_replaced(self):
        code = r'''
import sys, types
from pathlib import Path
import project_bootstrap
root = Path.cwd()
stale = types.ModuleType('sdof')
stale.__file__ = str(root / 'sdof.py')
stale.old_version = True
sys.modules['sdof'] = stale
foreign = types.ModuleType('plots')
foreign.__file__ = '/unrelated/plots.py'
sys.modules['plots'] = foreign
project_bootstrap.refresh_project_modules(root)
from sdof import System, metrics, time_history
import plots
assert callable(time_history)
assert len(time_history(System(), 1, 10)) == 10
assert metrics(System())['settling_s'] > 0
assert plots.System is System
assert not hasattr(sys.modules['sdof'], 'old_version')
first = sys.modules['sdof']
project_bootstrap.refresh_project_modules(root)
assert sys.modules['sdof'] is first
'''
        subprocess.run([sys.executable, '-c', textwrap.dedent(code)], cwd=ROOT,
                       check=True, capture_output=True, text=True)

    def test_source_change_refreshes_dependencies(self):
        code = r'''
from pathlib import Path
import tempfile, sys
import project_bootstrap
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    (root/'sdof.py').write_text('version = "old"\n')
    (root/'plots.py').write_text('from sdof import version\n')
    (root/'theory_ui.py').write_text('version = 1\n')
    project_bootstrap.refresh_project_modules(root)
    assert sys.modules['plots'].version == 'old'
    (root/'sdof.py').write_text('version = "new"\n')
    project_bootstrap.refresh_project_modules(root)
    assert sys.modules['plots'].version == 'new'
'''
        subprocess.run([sys.executable, '-c', textwrap.dedent(code)], cwd=ROOT,
                       check=True, capture_output=True, text=True)
