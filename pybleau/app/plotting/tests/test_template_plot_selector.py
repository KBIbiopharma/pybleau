from unittest import TestCase

from app_common.apptools.testing_utils import assert_obj_gui_works

from pybleau.app.plotting.template_plot_selector import \
    TemplatePlotNameSelector


class TestTemplatePlotSelector(TestCase):
    def test_bring_up_selector_popup(self):
        selector = TemplatePlotNameSelector()
        assert_obj_gui_works(selector)

    def test_new_name_is_valid(self):
        options = list('abcde')
        select = TemplatePlotNameSelector(string_options=options)
        select.replace_old_template = False

        # test when new name matches current template
        select.new_name = options[0]
        self.assertFalse(select.new_name_entry_is_valid)
        self.assertTrue(select.new_name_is_required_and_invalid)

        # test when new name is valid
        select.new_name = 'abcdefghijklmopqrstuvwxyz _ 1234567890'
        self.assertTrue(select.new_name_entry_is_valid)
        self.assertFalse(select.new_name_is_required_and_invalid)

        # test when new name has bad strings
        select.new_name = 'b$'
        self.assertFalse(select.new_name_entry_is_valid)
        self.assertTrue(select.new_name_is_required_and_invalid)

        # ensure new name is valid if replacing old template
        select.replace_old_template = True
        self.assertFalse(select.new_name_is_required_and_invalid)

    def test_input_is_valid(self):
        options = list('abcde')
        select = TemplatePlotNameSelector(string_options=options)
        select.replace_old_template = False
        select.new_name = 'abc'
        self.assertTrue(select.input_is_valid)
        select.replace_old_template = True
        self.assertFalse(select.input_is_valid)
        self.assertFalse(select.is_string_selected)
        select.selected_string = options[-1]
        self.assertTrue(select.input_is_valid)
        self.assertTrue(select.is_string_selected)
