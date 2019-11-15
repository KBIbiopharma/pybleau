from itertools import permutations
import plotly.graph_objs as go


class BaseFigureArguments(object):
    """ Base class to mixin to test all figure related arguments when testing
    plot makers.
    """
    def test_bad_arg(self):
        kwargs = {"non_existent": 45}
        self.assert_cannot_pass_kwargs(kwargs)

    def test_fig_title(self):
        kwargs = {"title": "BLAH"}
        self.assert_can_pass_kwargs(kwargs)

    def test_axis_scale(self):
        for val1, val2 in permutations([None, "linear", "log"], 2):
            kwargs = {"x_scale": val1, "y_scale": val2}
            self.assert_can_pass_kwargs(kwargs, msg=kwargs)

    def test_bad_axis_scale(self):
        kwargs = {"x_scale": "FOO", "y_scale": "linear"}
        self.assert_cannot_pass_kwargs(kwargs, msg=kwargs)

        kwargs = {"x_scale": "linear", "y_scale": "FOO"}
        self.assert_cannot_pass_kwargs(kwargs, msg=kwargs)

    def test_fig_sizes(self):
        kwargs = {"fig_width": 800, "fig_height": 800}
        self.assert_can_pass_kwargs(kwargs)

    def test_bad_fig_sizes(self):
        bad_kwargs = {"fig_width": 800, "fig_height": "BLAH"}
        self.assert_cannot_pass_kwargs(bad_kwargs)

    def test_x_tickangle(self):
        kwargs = {"x_tickangle": 45}
        self.assert_can_pass_kwargs(kwargs)

    def test_bad_x_tickangle_value(self):
        kwargs = {"x_tickangle": "BLAH"}
        self.assert_cannot_pass_kwargs(kwargs)

    # Additional assertion methods --------------------------------------------

    def assert_can_pass_kwargs(self, kwargs, msg=None):
        self.default_args.update(kwargs)
        fig = self.plot_func(data=self.data, **self.default_args)
        self.assert_valid_plotly_figure(fig, num_renderers=1, msg=msg)
        return fig

    def assert_cannot_pass_kwargs(self, kwargs, exception_type=Exception,
                                  msg=None):
        self.default_args.update(kwargs)
        with self.assertRaises(exception_type, msg=msg):
            self.plot_func(data=self.data, **self.default_args)

    def assert_valid_plotly_figure(self, fig, num_renderers=1,
                                   renderer_types=None, msg=None):
        if renderer_types is None:
            renderer_types = self.renderer_type

        self.assertIsInstance(fig, go.Figure)
        data = fig.data
        self.assertEqual(len(data), num_renderers, msg=msg)
        for i in range(num_renderers):
            self.assertIsInstance(data[i], renderer_types, msg=msg)
