from unittest import TestCase
from unittest.mock import MagicMock

from pybleau.app.plotting.renderer_style import BaseRendererStyle
from pybleau.app.utils.chaco_colors import generate_chaco_colors, \
    assign_renderer_colors


class TestColorGenerationAndAssignment(TestCase):
    def test_generate_colors_returns_correct_result(self):
        n_colors = 0
        result = generate_chaco_colors(n_colors)
        self.assertEqual(len(result), n_colors)
        n_colors = 12
        result = generate_chaco_colors(n_colors, palette="tab20")
        self.assertEqual(len(result), n_colors)

    def test_assign_renderer_colors(self):
        num_renderers = 5
        renderer_styles = \
            [MagicMock(BaseRendererStyle) for _ in range(num_renderers)]
        expected_colors = generate_chaco_colors(num_renderers)
        assign_renderer_colors(renderer_styles)
        actual_colors = [renderer.color for renderer in renderer_styles]
        self.assertCountEqual(actual_colors, expected_colors)
        expected_colors = generate_chaco_colors(num_renderers, palette="tab20")
        assign_renderer_colors(renderer_styles, palette="tab20")
        actual_colors = [renderer.color for renderer in renderer_styles]
        self.assertCountEqual(actual_colors, expected_colors)
