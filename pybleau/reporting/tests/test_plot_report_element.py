import pandas as pd
from unittest import TestCase
from plotly import graph_objs as go
import dash_core_components as dcc
import dash_html_components as html

from pandas.testing import assert_frame_equal

from pybleau.reporting.plot_report_element import PlotReportElement

DATA_ROWS = [{"index": 0, "efficiency": 1.1831148168148373, "break_point": 1.0, "final_yield": -0.13495587001387044, "break_point2": 1, "gain": -0.623538580994213, "disposed_batch": "a", "correlation": 1, "axial_disp": 1}, {"index": 1, "efficiency": -0.7213700305627939, "break_point": 2.0, "final_yield": 0.9821047883662166, "break_point2": 1, "gain": 1.3573835519883992, "disposed_batch": "b", "correlation": 2, "axial_disp": 2}, {"index": 2, "efficiency": 2.5869811660417548, "break_point": 3.0, "final_yield": 1.432876322816532, "break_point2": 1, "gain": 1.086212379289521, "disposed_batch": "a", "correlation": 3, "axial_disp": 3}, {"index": 3, "efficiency": -0.5535593467318864, "break_point": 4.0, "final_yield": 0.29821388132495735, "break_point2": 1, "gain": 1.33983703636284, "disposed_batch": "b", "correlation": 4, "axial_disp": 4}, {"index": 4, "efficiency": -0.6256106462607908, "break_point": 1.0, "final_yield": -1.3641145090543807, "break_point2": 2, "gain": 2.5112766921798637, "disposed_batch": "c", "correlation": 5, "axial_disp": 1}, {"index": 5, "efficiency": -2.05897697458559, "break_point": 2.0, "final_yield": 0.0024307551390565204, "break_point2": 2, "gain": 0.6971698898321809, "disposed_batch": "a", "correlation": 6, "axial_disp": 2}, {"index": 6, "efficiency": 0.1119537227147169, "break_point": 3.0, "final_yield": 1.4343665535207522, "break_point2": 2, "gain": -1.4708451312086304, "disposed_batch": "b", "correlation": 7, "axial_disp": 3}, {"index": 7, "efficiency": 0.20775896223764828, "break_point": 4.0, "final_yield": 0.29945723323495965, "break_point2": 2, "gain": -0.5956562432148557, "disposed_batch": "c", "correlation": 8, "axial_disp": 4}, {"index": 8, "efficiency": -0.9475447426875377, "break_point": 1.0, "final_yield": 0.4972208265694213, "break_point2": 3, "gain": -0.1468784389073114, "disposed_batch": "d", "correlation": 9, "axial_disp": 1}, {"index": 9, "efficiency": 0.9871567262524245, "break_point": 2.0, "final_yield": 1.3354072226357265, "break_point2": 3, "gain": -0.5478997121945572, "disposed_batch": "a", "correlation": 10, "axial_disp": 2}, {"index": 10, "efficiency": 0.07947607694031913, "break_point": 3.0, "final_yield": 0.6297449470005222, "break_point2": 3, "gain": -0.47016525688095584, "disposed_batch": "b", "correlation": 11, "axial_disp": 3}, {"index": 11, "efficiency": 1.4735672608947816, "break_point": 4.0, "final_yield": 0.7624858433386921, "break_point2": 3, "gain": 1.4961334231512595, "disposed_batch": "c", "correlation": 12, "axial_disp": 4}, {"index": 12, "efficiency": -1.0579542276575313, "break_point": 1.0, "final_yield": -0.24314395008351022, "break_point2": 4, "gain": -0.720935882536975, "disposed_batch": "d", "correlation": 13, "axial_disp": 1}, {"index": 13, "efficiency": 0.25376216181196126, "break_point": 2.0, "final_yield": 1.6920470529644995, "break_point2": 4, "gain": -0.7488702229756584, "disposed_batch": "e", "correlation": 14, "axial_disp": 2}, {"index": 14, "efficiency": 1.1752387120960943, "break_point": 3.0, "final_yield": 0.9110843602861356, "break_point2": 4, "gain": -0.8914396150093356, "disposed_batch": "a", "correlation": 15, "axial_disp": 3}, {"index": 15, "efficiency": -1.4035429580570882, "break_point": 0., "final_yield": -0.49811214613026095, "break_point2": 4, "gain": -1.073120350853674, "disposed_batch": "b", "correlation": 16, "axial_disp": 4}]  # noqa

DATA_DF = pd.DataFrame(DATA_ROWS).set_index("index")

SCATT_DESC = {
    "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
    "data": {
        "values": DATA_ROWS
    },
    "encoding": {
        "y": {"field": "efficiency", "type": "quantitative"},
        "x": {"field": "final_yield", "type": "quantitative"},
    },
    "mark": "point"
}


SCATT_DESC2 = {
    "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
    "data": {
        "values": DATA_ROWS
    },
    "encoding": {
        "y": {"field": "efficiency", "type": "quantitative"},
        "x": {"field": "final_yield", "type": "quantitative"},
        "color": {"field": "disposed_batch", "type": "ordinal"}},
    "mark": "point"
}


class TestPlotReportElement(TestCase):
    def setUp(self):
        self.scatt_desc = SCATT_DESC

    def test_create_no_arg(self):
        element = PlotReportElement()
        self.assertIsNone(element.source_data)
        self.assertEqual(element.plot_desc, {})

    def test_create_from_valid_description_no_data(self):
        data = self.scatt_desc.pop("data")
        try:
            element = PlotReportElement(plot_desc=self.scatt_desc)
            self.assertIsNone(element.source_data)
            self.assertEqual(element.plot_desc, self.scatt_desc)
        finally:
            self.scatt_desc["data"] = data

    def test_create_from_valid_description_pass_data_directly(self):
        data = self.scatt_desc.pop("data")
        try:
            element = PlotReportElement(plot_desc=self.scatt_desc,
                                        source_data=DATA_DF)
            self.assertIs(element.source_data, DATA_DF)
            self.assertEqual(element.plot_desc, self.scatt_desc)
        finally:
            self.scatt_desc["data"] = data

    def test_create_from_valid_description_with_data(self):
        element = PlotReportElement(plot_desc=self.scatt_desc)
        assert_frame_equal(element.source_data, DATA_DF)
        expected = {key: val for key, val in self.scatt_desc.items()
                    if key != "data"}
        self.assertEqual(element.plot_desc, expected)


class TestPlotReportElementToDash(TestCase):
    def setUp(self):
        self.scatt_desc = SCATT_DESC

    def test_export_scatter_to_dash(self):
        element = PlotReportElement(plot_desc=self.scatt_desc)
        dash_elements = element.to_dash()
        self.assertEqual(len(dash_elements), 1)
        self.assert_scatter_present(dash_elements)

    def test_export_colored_scatter_to_dash(self):
        element = PlotReportElement(plot_desc=SCATT_DESC2)
        dash_elements = element.to_dash()
        self.assertEqual(len(dash_elements), 1)
        num_scatters = len(DATA_DF["disposed_batch"].unique())
        self.assert_scatter_present(dash_elements,
                                    num_scatters=num_scatters)

    def test_export_garbage_to_dash(self):
        element = PlotReportElement(plot_desc={"foo": "bar"})
        dash_elements = element.to_dash()
        self.assertEqual(len(dash_elements), 1)
        self.assertIsInstance(dash_elements[0], dcc.Graph)
        self.assertIsInstance(dash_elements[0].figure, go.Figure)
        self.assertEqual(dash_elements[0].figure.data, ())

    def test_export_scatter_to_report_dash(self):
        element = PlotReportElement(plot_desc=self.scatt_desc)
        dash_elements = element.to_report(backend="dash")
        self.assertEqual(len(dash_elements), 1)
        self.assert_scatter_present(dash_elements)

    def test_export_scatter_to_dash_w_description(self):
        self.scatt_desc["description"] = "BLAH"
        try:
            element = PlotReportElement(plot_desc=self.scatt_desc)
            dash_elements = element.to_dash()
            self.assertEqual(len(dash_elements), 2)
            self.assert_scatter_present(dash_elements)
            self.assertIsInstance(dash_elements[1], html.P)
        finally:
            self.scatt_desc.pop("description")

    def test_export_scatter_to_report_dash_w_description(self):
        self.scatt_desc["description"] = "BLAH"
        try:
            element = PlotReportElement(plot_desc=self.scatt_desc)
            dash_elements = element.to_report(backend="dash")
            self.assertEqual(len(dash_elements), 2)
            self.assert_scatter_present(dash_elements)
            self.assertIsInstance(dash_elements[1], html.P)
        finally:
            self.scatt_desc.pop("description")

    # Assertion methods -------------------------------------------------------

    def assert_scatter_present(self, dash_elements, num_scatters=1):
        graph = dash_elements[0]
        self.assertIsInstance(graph, dcc.Graph)
        self.assertIsInstance(graph.figure, go.Figure)
        self.assertIsInstance(graph.figure.data, tuple)
        self.assertEqual(len(graph.figure.data), num_scatters)
        for i in range(num_scatters):
            self.assertIsInstance(graph.figure.data[i], go.Scatter)
