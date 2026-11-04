"""Streamlit Community Cloud launch file for the SDOF sensitivity app.

Deploy this repository with main file path: streamlit.py.
The import bridge prevents this filename from hiding the installed package.
"""
import importlib.machinery
import importlib.util
from pathlib import Path
import runpy
import sys


def _installed_streamlit():
    root = Path(__file__).resolve().parent
    search_path = [
        entry for entry in sys.path
        if Path(entry or ".").resolve() != root
    ]
    spec = importlib.machinery.PathFinder.find_spec("streamlit", search_path)
    if spec is None or spec.loader is None or spec.submodule_search_locations is None:
        raise ImportError("Install the project dependencies: pip install -r requirements.txt")
    package = importlib.util.module_from_spec(spec)
    sys.modules["streamlit"] = package
    spec.loader.exec_module(package)
    return package


if __name__ == "streamlit":
    # Support imports from app.py, tests and other project modules.
    _installed_streamlit()
elif __name__ == "__main__" and getattr(__spec__, "name", None) == "streamlit":
    # Support: python -m streamlit run streamlit.py
    _installed_streamlit()
    runpy.run_module("streamlit", run_name="__main__", alter_sys=True)
elif __name__ == "__main__":
    # Streamlit's script runner executes the selected file as __main__.
    runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
