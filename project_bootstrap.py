"""Refresh local dependencies after a live source update, without reloading Streamlit.

Streamlit reruns entry scripts, but previously imported helper modules may remain
in sys.modules. Fingerprints detect changed project sources across reruns.
"""
import hashlib
import importlib
import importlib.util
from pathlib import Path
import runpy
import sys
from threading import RLock

_MODULES = ('sdof', 'plots', 'theory_ui')
_lock = RLock()
_loaded_signature = None
_loaded_modules = {}


def refresh_project_modules(root):
    """Load exact repository files in dependency order on first use or change."""
    global _loaded_signature, _loaded_modules
    root = Path(root).resolve()
    with _lock:
        sources = {name: (root / (name + '.py')).read_bytes() for name in _MODULES}
        signature = tuple((name, hashlib.sha256(source).hexdigest())
                          for name, source in sources.items())
        signature = (str(root), signature)
        modules_present = all(
            name in sys.modules
            and sys.modules[name] is _loaded_modules.get(name)
            and Path(getattr(sys.modules[name], '__file__', '')).resolve() == root / (name + '.py')
            for name in _MODULES
        )
        if signature == _loaded_signature and modules_present:
            return
        importlib.invalidate_caches()
        previous = {name: sys.modules.get(name) for name in _MODULES}
        try:
            for name in _MODULES:
                spec = importlib.util.spec_from_file_location(name, root / (name + '.py'))
                if spec is None or spec.loader is None:
                    raise ImportError(f'Unable to load project module: {name}')
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                # Compile current bytes so equal-size, same-second updates cannot
                # reuse an older timestamp-based .pyc file.
                exec(compile(sources[name], str(root / (name + '.py')), 'exec'), module.__dict__)
        except BaseException:
            # Do not leave a partially refreshed dependency set behind.
            for name, module in previous.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module
            raise
        _loaded_signature = signature
        _loaded_modules = {name: sys.modules[name] for name in _MODULES}


def run_app(root):
    root = Path(root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    refresh_project_modules(root)
    runpy.run_path(str(root / 'app.py'), run_name='__main__')
