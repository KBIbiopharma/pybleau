from unittest import skipUnless, TestCase
import os

from app_common.apptools.testing_utils import temp_bringup_ui_for
try:
    from pybleau.app.api import FilterExpression, FilterExpressionManager
except ImportError:
    pass

if os.environ.get("ETS_TOOLKIT", "qt4") == "null":
    ui_available = False
else:
    ui_available = True


@skipUnless(ui_available, "NO UI BACKEND AVAILABLE")
class TestFilterExpressionManager(TestCase):

    def test_create(self):
        manager = FilterExpressionManager()
        self.assertEqual(manager.known_filter_exps, [])
        self.assertEqual(manager.displayed_filter_exps, [])
        self.assertIsNone(manager.selected_expression)
        self.assertEqual(manager.mode, "load")
        self.assertEqual(manager.search_names, "")
        self.assertEqual(manager.search_expressions, "")

    def test_create_with_known_exps(self):
        exps = [FilterExpression(expression=char) for char in "abcedfg"]
        manager = FilterExpressionManager(known_filter_exps=exps)
        self.assertEqual(len(manager.known_filter_exps), len(exps))
        for exp in manager.known_filter_exps:
            self.assertEqual(exp.name, exp.expression)

        self.assertEqual(len(manager.displayed_filter_exps), len(exps))
        self.assertEqual(manager._known_expressions, set("abcedfg"))
        self.assertIsNone(manager.selected_expression)
        self.assertEqual(manager.search_names, "")
        self.assertEqual(manager.search_expressions, "")

    def test_bring_up(self):
        manager = FilterExpressionManager()
        with temp_bringup_ui_for(manager):
            pass

    def test_bring_up_load_mode(self):
        exps = [FilterExpression(expression=char) for char in "abcedfg"]
        manager = FilterExpressionManager(known_filter_exps=exps)
        manager.selected_expression = exps[1]
        with temp_bringup_ui_for(manager, kind="live"):
            pass

        # Make sure once the UI is closed, the data the DF Analyzer needs is
        # intact:
        self.assertIs(manager.selected_expression, exps[1])

    def test_bring_up_manage_mode(self):
        exps = [FilterExpression(expression=char) for char in "abcedfg"]
        manager = FilterExpressionManager(known_filter_exps=exps,
                                          mode="manage")
        manager.selected_expression = exps[1]
        with temp_bringup_ui_for(manager, kind="live"):
            manager._delete_button_fired()

        # Make sure once the UI is closed, the data the DF Analyzer needs is
        # intact:
        self.assertEqual(len(manager.known_filter_exps), len(exps)-1)
        self.assertEqual([x.name for x in manager.known_filter_exps],
                         list("acedfg"))
        self.assertEqual([x.expression for x in manager.known_filter_exps],
                         list("acedfg"))

    def test_search_expressions(self):
        exps = [FilterExpression(expression=char+">1") for char in "aabc"]
        num_expr = 4
        manager = FilterExpressionManager(known_filter_exps=exps, mode="load")

        manager.search_expressions = "a"
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), 2)

        # Space doesn't matter:
        manager.search_expressions = "a>1"
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), 2)

        manager.search_expressions = ""
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), num_expr)

        manager.search_expressions = "b"
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), 1)

        manager.search_expressions = "z"
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), 0)

        manager.search_expressions = "   "
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), num_expr)

    def test_search_names(self):
        # Add another entry containing a:
        exps = [FilterExpression(expression=char+">1")
                for char in "aabc"]
        exps[0].name = "blah"
        num_expr = 4
        manager = FilterExpressionManager(known_filter_exps=exps, mode="load")

        manager.search_names = "a"
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), 2)

        manager.search_names = "b"
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), 2)

        manager.search_names = ""
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), num_expr)

        manager.search_names = "c"
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), 1)

        manager.search_names = "bla"
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), 1)

        manager.search_names = "   "
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), num_expr)

        manager.search_names = "z"
        self.assertEqual(len(manager.known_filter_exps), num_expr)
        self.assertEqual(len(manager.displayed_filter_exps), 0)
