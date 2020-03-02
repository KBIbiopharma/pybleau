
from unittest import TestCase
from traits.testing.unittest_tools import UnittestTools

from pybleau.app.io.serializer import serialize
from pybleau.app.plotting.renderer_style import BarRendererStyle, \
    HeatmapRendererStyle, CmapScatterRendererStyle, LineRendererStyle, \
    ScatterRendererStyle
from pybleau.app.utils.string_definitions import DEFAULT_CONTIN_PALETTE


class BaseSerialDataTest(UnittestTools):

    def test_serialize_default_plot_style(self):
        obj = self.renderer_style()
        serial_obj = serialize(obj)
        for trait, val in self.default_traits.items():
            self.assert_serial_attr_equal(serial_obj, trait, val)

    def test_serialize_non_default_plot_style(self):
        obj = self.renderer_style(**self.traits1)
        serial_obj = serialize(obj)
        self.default_traits.update(self.traits1)
        for trait, val in self.default_traits.items():
            self.assert_serial_attr_equal(serial_obj, trait, val)

    def test_serialize_non_default_plot_style2(self):
        obj = self.renderer_style(**self.traits2)
        serial_obj = serialize(obj)
        self.default_traits.update(self.traits2)
        for trait, val in self.default_traits.items():
            self.assert_serial_attr_equal(serial_obj, trait, val)

    # Utilities ---------------------------------------------------------------

    def assert_serial_attr_equal(self, serial_obj, attr="", value=None):
        serial_val = serial_obj[0]["data"][attr]
        if isinstance(serial_val, dict):
            klass = eval(serial_val['class_metadata']['type'])
            serial_val = klass(serial_val['data'])

        self.assertEqual(serial_val, value,
                         msg="{} not equal to {}".format(attr, value))


class TestSerializeLineRendererStyles(TestCase, BaseSerialDataTest):
    def setUp(self):
        self.renderer_style = LineRendererStyle
        self.default_traits = dict(color="blue", alpha=1.0, line_style='solid')
        self.traits1 = dict(line_style='dash')
        self.traits2 = dict(color="red", line_style='dash', alpha=0.5)


class TestSerializeScatterRendererStyles(TestCase, BaseSerialDataTest):
    def setUp(self):
        self.renderer_style = ScatterRendererStyle
        self.default_traits = dict(color="blue", alpha=1.0, marker='circle',
                                   marker_size=6)
        self.traits1 = dict(marker_size=10)
        self.traits2 = dict(color="red", marker_size=10, alpha=0.5)


class TestSerializeBarRendererStyles(TestCase, BaseSerialDataTest):
    def setUp(self):
        self.renderer_style = BarRendererStyle
        self.default_traits = dict(color="blue", alpha=1.0, bar_width=0.)
        self.traits1 = dict(line_color="red")
        self.traits2 = dict(line_color="red", bar_width=0.5, alpha=0.5)


class TestSerializeCmapScatterRendererStyles(TestCase, BaseSerialDataTest):
    def setUp(self):
        self.renderer_style = CmapScatterRendererStyle
        self.default_traits = dict(color_palette=DEFAULT_CONTIN_PALETTE,
                                   fill_alpha=1.0, marker="circle",
                                   marker_size=6)
        self.traits1 = dict(fill_alpha=0.5)
        self.traits2 = dict(fill_alpha=0.5, color_palette="bone",
                            marker="triangle")

    def test_color_palette_controls_colormap(self):
        style = CmapScatterRendererStyle()
        with self.assertTraitChanges(style, "color_mapper", 1):
            style.color_palette = "bone"


class TestSerializeCmapHeatmapRendererStyles(TestCase, BaseSerialDataTest):
    def setUp(self):
        self.renderer_style = HeatmapRendererStyle
        self.default_traits = dict(color_palette=DEFAULT_CONTIN_PALETTE,
                                   xbounds=(0, 1), ybounds=(0, 1))
        self.traits1 = dict(xbounds=(2, 3))
        self.traits2 = dict(xbounds=(2, 3), color_palette="bone",
                            ybounds=(3, 5))
