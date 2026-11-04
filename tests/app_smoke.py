import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]

class AppSmoke(unittest.TestCase):
    def test_controls_edge_cases_and_all_pages(self):
        app=AppTest.from_file(str(ROOT/'streamlit.py'),default_timeout=90).run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'1.5915 Hz')
        app.number_input(key='mass').set_value(4000.).run()
        self.assertEqual(app.metric[0].value,'0.79577 Hz')
        self.assertEqual(len(app.exception),0)
        app.number_input(key='damping').set_value(0.).run()
        self.assertEqual(app.metric[3].value,'Never settles')
        app.number_input(key='v0').set_value(0.).run()
        self.assertEqual(app.metric[3].value,'0 s')
        app.number_input(key='x0').set_value(.1).run()
        self.assertEqual(app.metric[3].value,'Never settles')
        app.number_input(key='damping').set_value(100000.).run()
        self.assertEqual(app.metric[2].value,'N/A')
        app.radio(key='page').set_value('Sensitivity').run()
        self.assertEqual(len(app.exception),0)
        app.radio(key='page').set_value('Compare').run()
        app.selectbox(key='comparison_quantity').set_value('acceleration').run()
        self.assertEqual(len(app.exception),0)
        app.radio(key='page').set_value('Concepts & mathematics').run()
        self.assertEqual(len(app.exception),0)
        self.assertGreater(len(app.latex),15)
        app.radio(key='page').set_value('Downloads').run()
        self.assertEqual(len(app.exception),0)
        app.selectbox(key='damping_mode').set_value('Damping ratio ζ').run()
        app.number_input(key='zeta_input').set_value(1.).run()
        self.assertEqual(app.metric[1].value,'1')
        self.assertEqual(len(app.exception),0)

    def test_launcher_recovers_a_cached_old_solver(self):
        import sys
        import types
        stale=types.ModuleType('sdof')
        stale.__file__=str(ROOT/'sdof.py')
        sys.modules['sdof']=stale
        app=AppTest.from_file(str(ROOT/'streamlit.py'),default_timeout=90).run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.metric),4)
        self.assertTrue(callable(sys.modules['sdof'].time_history))
