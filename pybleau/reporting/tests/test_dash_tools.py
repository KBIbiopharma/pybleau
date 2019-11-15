from unittest import TestCase
from os.path import dirname, join
import dash
import dash_html_components as html
import dash_core_components as dcc
from flask import Flask

from pybleau.reporting.dash_tools import analysis_file2dash_reporter
from pybleau.reporting.dash_reporter import DashReporter
from pybleau.reporting.base_report_element import BaseReportElement
from pybleau.reporting.plot_report_element import PlotReportElement
import pybleau

HERE = dirname(__file__)

PKG_DIR = dirname(pybleau.__file__)


class TestAnalysisToDashReporter(TestCase):
    def setUp(self):
        self.analysis_file1 = join(HERE, "sample_1_plot_analysis.json")
        self.analysis_file2 = join(HERE, "sample_5_plot_analysis.json")
        self.logo_path = join(PKG_DIR, "images", "KBILogo.png")
        self.backend = "dash"

    def test_build_1_plot_report_no_explorer(self):
        reporter = analysis_file2dash_reporter(self.analysis_file1,
                                               include_explorers=False)
        self.assert_reporter_is_built(reporter)
        self.assertEqual(len(reporter.report_elements), 1)
        self.assertIsInstance(reporter.report_elements[0], PlotReportElement)
        children = reporter.dash_app.layout.children
        # By default, there is a title and a plot
        self.assertEqual(len(children), 2)
        self.assertIsInstance(children[0], html.H1)
        self.assertIsInstance(children[1], dcc.Graph)

    def test_build_1_plot_report_w_explorer(self):
        reporter = analysis_file2dash_reporter(self.analysis_file1,
                                               include_explorers=True)
        self.assert_reporter_is_built(reporter)
        # 2 elements: the plot and the explorer:
        self.assertEqual(len(reporter.report_elements), 2)
        self.assertIsInstance(reporter.report_elements[0], PlotReportElement)
        children = reporter.dash_app.layout.children
        # A title and a plot, a subtitle, 2 drop down sets and an explorer plot
        self.assertEqual(len(children), 6)
        self.assertIsInstance(children[0], html.H1)
        self.assertIsInstance(children[1], dcc.Graph)
        self.assert_are_valid_df_explorer(children[2:])

    def test_build_1_plot_report_complete(self):
        reporter = analysis_file2dash_reporter(
            self.analysis_file1, include_explorers=True,
            report_logo=self.logo_path
        )
        self.assert_reporter_is_built(reporter)
        # 2 elements: the plot and the explorer:
        self.assertEqual(len(reporter.report_elements), 2)
        self.assertIsInstance(reporter.report_elements[0], PlotReportElement)
        children = reporter.dash_app.layout.children
        # A logo, a title and a plot, a subtitle, 2 drop down sets and an
        # explorer plot:
        self.assertEqual(len(children), 7)
        self.assert_child_is_image(children[0])
        self.assertIsInstance(children[1], html.H1)
        self.assertIsInstance(children[2], dcc.Graph)
        self.assert_are_valid_df_explorer(children[3:])

    def test_build_5_plot_report(self):
        reporter = analysis_file2dash_reporter(
            self.analysis_file2, include_explorers=True,
            report_logo=self.logo_path
        )
        self.assert_reporter_is_built(reporter)
        # 6 elements: 5 plot and the explorer:
        self.assertEqual(len(reporter.report_elements), 6)
        self.assertIsInstance(reporter.report_elements[0], PlotReportElement)
        children = reporter.dash_app.layout.children
        # A logo, a title, 5 plot, a subtitle, 2 drop down sets and an
        # explorer plot:
        self.assertEqual(len(children), 11)
        self.assert_child_is_image(children[0])
        self.assertIsInstance(children[1], html.H1)
        for i in range(2, 2+5):
            self.assertIsInstance(children[i], dcc.Graph)
        self.assert_are_valid_df_explorer(children[7:])

    # Assertion functions -----------------------------------------------------

    def assert_reporter_is_built(self, reporter):
        self.assertEqual(reporter.backend, self.backend)
        self.assertIsInstance(reporter, DashReporter)
        self.assertIsInstance(reporter.dash_app, dash.Dash)
        self.assertIsInstance(reporter.flask_app, Flask)

        for element in reporter.report_elements:
            self.assertIsInstance(element, BaseReportElement)

        layout = reporter.dash_app.layout
        self.assertIsInstance(layout, html.Div)

    def assert_are_valid_df_explorer(self, dash_elem_list):
        # Sub-section title:
        self.assertIsInstance(dash_elem_list[0], html.H2)
        # First and second set of drop downs:
        self.assert_is_dropdown_group(dash_elem_list[1])
        self.assert_is_dropdown_group(dash_elem_list[2])
        # The plotter:
        self.assertIsInstance(dash_elem_list[3], html.Div)
        self.assertEqual(len(dash_elem_list[3].children), 1)
        self.assertIsInstance(dash_elem_list[3].children[0], dcc.Graph)

    def assert_is_dropdown_group(self, group):
        self.assertIsInstance(group, html.Div)
        children = group.children
        self.assertIsInstance(children[0], html.P)
        self.assertIsInstance(children[1], dcc.Dropdown)
        self.assertIsInstance(children[2], html.P)
        self.assertIsInstance(children[3], dcc.Dropdown)

    def assert_child_is_image(self, element):
        self.assertIsInstance(element, html.Div)
        self.assertEqual(len(element.children), 1)
        self.assertIsInstance(element.children[0], html.Img)
