import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

class AppSmoke(unittest.TestCase):
    def test_default_and_overdamped(self):
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'),default_timeout=60).run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.metric),4)
        app.number_input[2].set_value(40000.0).run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[1].value,'2.0000')
        app.toggle[0].set_value(False).run()
        self.assertEqual(len(app.exception),0)
