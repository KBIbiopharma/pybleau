import os
from unittest import skipIf, TestCase
from traits.testing.unittest_tools import UnittestTools

from app_common.apptools.testing_utils import assert_obj_gui_works

try:
    from pybleau.app.plotting.renderer_style import BarRendererStyle, \
        HeatmapRendererStyle, CmapScatterRendererStyle, LineRendererStyle,\
        ScatterRendererStyle
except ImportError:
    pass

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestRendererStyleAsView(TestCase):
    """ Make sure any styling renderer object can be brought up as views.
    """
    def test_open_bar_renderer_style_as_view(self):
        assert_obj_gui_works(BarRendererStyle())

    def test_open_line_renderer_style_as_view(self):
        assert_obj_gui_works(LineRendererStyle())

    def test_open_scatter_renderer_style_as_view(self):
        assert_obj_gui_works(ScatterRendererStyle())

    def test_open_heatmap_renderer_style_as_view(self):
        assert_obj_gui_works(HeatmapRendererStyle())

    def test_open_cmap_scatter_renderer_style_as_view(self):
        assert_obj_gui_works(CmapScatterRendererStyle())


class TestCmapHeatmapRendererStyle(TestCase, UnittestTools):

    def test_color_palette_controls_colormap(self):
        style = HeatmapRendererStyle()
        with self.assertTraitChanges(style, "colormap", 1):
            style.color_palette = "bone"

    def test_reset_bounds(self):
        style = HeatmapRendererStyle(xbounds=(2, 4), ybounds=(1, 3))
        self.assertEqual(style.auto_xbounds, style.xbounds)
        self.assertEqual(style.auto_ybounds, style.ybounds)

        style.xbounds = (3, 4)
        style.reset_xbounds = True
        self.assertEqual(style.auto_xbounds, style.xbounds)

        style.xbounds = (3, 4)
        style.reset_xbounds = True
        self.assertEqual(style.auto_ybounds, style.ybounds)
