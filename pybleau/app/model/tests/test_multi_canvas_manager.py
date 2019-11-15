from unittest import skipIf, TestCase

try:
    from chaco.api import Plot

    from pybleau.app.model.plot_descriptor import PlotDescriptor
    from pybleau.app.model.multi_canvas_manager import \
        ConstraintsPlotContainerManager, DEFAULT_NUM_CONTAINERS, \
        MultiCanvasManager

    no_gui_toolkit = False
except ImportError:
    no_gui_toolkit = True


@skipIf(no_gui_toolkit, "NO GUI toolkit!")
class TestMultiCanvasManager(TestCase):
    def test_create_default(self):
        canvas = MultiCanvasManager()
        self.assert_valid_canvas(canvas)

    def test_create_custom_num_manager(self):
        canvas = MultiCanvasManager(num_container_managers=3)
        self.assert_valid_canvas(canvas, num_managers=3)

    def test_create_custom_manager_list(self):
        manager = ConstraintsPlotContainerManager()
        canvas = MultiCanvasManager(container_managers=[manager])
        self.assert_valid_canvas(canvas, num_managers=1)
        self.assertIs(manager, canvas.container_managers[0])

    def test_create_custom_layout(self):
        canvas = MultiCanvasManager(layout_spacing=130)
        self.assert_valid_canvas(canvas)
        for manager in canvas.container_managers:
            self.assertEqual(manager.layout_spacing, 130)

    def test_add_plot(self):
        canvas = MultiCanvasManager()
        plot = Plot()
        desc = PlotDescriptor(plot=plot)
        canvas.add_plot_to_container(desc)
        self.assert_valid_canvas(canvas, num_plots=1)

    def test_add_plot_to_custom_container(self):
        canvas = MultiCanvasManager()
        plot = Plot()
        desc = PlotDescriptor(plot=plot)
        canvas.add_plot_to_container(desc, container=1)
        self.assert_valid_canvas(canvas, cont_idx=1, num_plots=1)

    def test_add_plot_to_custom_container2(self):
        canvas = MultiCanvasManager()
        plot = Plot()
        desc = PlotDescriptor(plot=plot)
        canvas.add_plot_to_container(desc,
                                     container=canvas.container_managers[2])
        self.assert_valid_canvas(canvas, cont_idx=2, num_plots=1)

    def test_add_remove_plot(self):
        canvas = MultiCanvasManager()
        plot = Plot()
        desc = PlotDescriptor(plot=plot)
        canvas.add_plot_to_container(desc)
        self.assert_valid_canvas(canvas, num_plots=1)
        canvas.remove_plot_from_container(desc)
        self.assert_valid_canvas(canvas, num_plots=0)

    def test_change_num_container(self):
        canvas = MultiCanvasManager()
        self.assert_valid_canvas(canvas)
        canvas.num_container_managers = 3
        self.assert_valid_canvas(canvas, num_managers=3)

    # Assertion methods -------------------------------------------------------

    def assert_valid_canvas(self, canvas, num_managers=None, cont_idx=0,
                            num_plots=0):
        if num_managers is None:
            num_managers = DEFAULT_NUM_CONTAINERS

        self.assertEqual(len(canvas.container_managers),
                         num_managers)
        for i, manager in enumerate(canvas.container_managers):
            self.assertIsNotNone(manager.container)
            contained_plots = manager.container.components
            if i == cont_idx:
                self.assertEqual(len(contained_plots), num_plots)
            else:
                self.assertEqual(len(contained_plots), 0)
