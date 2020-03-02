
from unittest import TestCase
from traits.testing.unittest_tools import UnittestTools

from app_common.traits.assertion_utils import assert_has_traits_almost_equal
from app_common.apptools.io.assertion_utils import assert_roundtrip_identical,\
    assert_file_roundtrip_identical

from pybleau.app.io.serializer import serialize
from pybleau.app.io.deserializer import deserialize
from pybleau.app.plotting.renderer_style import BarRendererStyle, \
    HeatmapRendererStyle, CmapScatterRendererStyle, LineRendererStyle, \
    ScatterRendererStyle
from pybleau.app.plotting.plot_style import SingleLinePlotStyle, \
    SingleScatterPlotStyle, TitleStyle, AxisStyle
from pybleau.app.plotting.histogram_plot_style import HistogramPlotStyle
from pybleau.app.plotting.heatmap_plot_style import HeatmapPlotStyle
from pybleau.app.plotting.bar_plot_style import BarPlotStyle
from pybleau.app.utils.string_definitions import DEFAULT_CONTIN_PALETTE


class BaseSerialDataTest(UnittestTools):

    def setUp(self):
        title_style = TitleStyle(font_size=12, font_name="roman")
        self.non_default_title_kw = {"title_style": title_style}
        axis_style1 = AxisStyle(range_low=12, title_style=title_style)
        axis_style2 = AxisStyle(range_high=3)
        self.non_default_axis_kw = [
            {"x_axis_style": axis_style1},
            {"y_axis_style": axis_style2},
            {"x_axis_style": axis_style2, "y_axis_style": axis_style1}
        ]

    def test_default_plot_style(self):
        obj = self.plot_style()
        self.assert_roundtrip_identical(obj)

    def test_non_default_title_plot_style(self):
        obj = self.plot_style(**self.non_default_title_kw)
        self.assert_roundtrip_identical(obj)

    def test_non_default_axis_plot_style(self):
        for kw in self.non_default_axis_kw:
            obj = self.plot_style(**kw)
            self.assert_roundtrip_identical(obj)

    def test_non_default_renderer_plot_style(self):
        for kw in self.non_default_axis_kw:
            obj = self.plot_style(**kw)
            self.assert_roundtrip_identical(obj)

    def assert_roundtrip_identical(self, obj):
        assert_roundtrip_identical(obj, serial_func=serialize,
                                   deserial_func=deserialize)


class TestRoundtripSingleLinePlotStyles(BaseSerialDataTest, TestCase):
    def setUp(self):
        self.plot_style = SingleLinePlotStyle
        super(TestRoundtripSingleLinePlotStyles, self).setUp()
        self.non_default_renderer_kw = [
            {"renderer_styles": [LineRendererStyle(color="red")]},
            {"renderer_styles": [LineRendererStyle(color="red", alpha=0.5)]},
        ]


class TestRoundtripScatterPlotStyle(BaseSerialDataTest, TestCase):
    def setUp(self):
        self.plot_style = SingleScatterPlotStyle
        super(TestRoundtripScatterPlotStyle, self).setUp()
        self.non_default_renderer_kw = [
            {"renderer_styles": [ScatterRendererStyle(color="red",
                                                      marker_size=10)]},
            {"renderer_styles": [ScatterRendererStyle(alpha=0.5,
                                                      marker="square")]},
            {"renderer_styles": [CmapScatterRendererStyle(color_palette="bone")]},  # noqa
        ]


class TestRoundtripBarPlotStyle(BaseSerialDataTest, TestCase):
    def setUp(self):
        self.plot_style = BarPlotStyle
        super(TestRoundtripBarPlotStyle, self).setUp()
        self.non_default_renderer_kw = [
            {"renderer_styles": [BarRendererStyle(fill_color="red")]},
            {"renderer_styles": [BarRendererStyle(line_color="red",
                                                  bar_width=0.5)]},
        ]


class TestRoundtripHistogramPlotStyle(BaseSerialDataTest, TestCase):
    def setUp(self):
        self.plot_style = HistogramPlotStyle
        super(TestRoundtripHistogramPlotStyle, self).setUp()
        self.non_default_renderer_kw = [
            {"renderer_styles": [BarRendererStyle(fill_color="red")]},
            {"renderer_styles": [BarRendererStyle(line_color="red",
                                                  bar_width=0.5)]},
        ]

    def test_aroundtrip_additional_attrs(self):
        obj = HistogramPlotStyle(bar_width=2)
        self.assert_roundtrip_identical(obj)

        obj = HistogramPlotStyle(num_bins=20)
        self.assert_roundtrip_identical(obj)


class TestRoundtripHeatmapPlotStyle(BaseSerialDataTest, TestCase):
    def setUp(self):
        self.plot_style = HeatmapPlotStyle
        super(TestRoundtripHeatmapPlotStyle, self).setUp()
        self.non_default_renderer_kw = [
            {"renderer_styles": [
                HeatmapRendererStyle(color_palette="bone", alpha=0.3)]},
        ]
