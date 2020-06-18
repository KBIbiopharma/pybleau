
from chaco.base_plot_container import BasePlotContainer
from traits.api import Any, Bool, Button, Enum, Event, HasStrictTraits, \
    Instance, Str

from pybleau.app.plotting.plot_config import BasePlotConfigurator
from pybleau.app.plotting.base_factories import BasePlotFactory
from ..plotting.api import PLOT_TYPES
from ..utils.string_definitions import CMAP_SCATTER_PLOT_TYPE

CONTAINER_IDX_REMOVAL = "delete"

CUSTOM_PLOT_TYPE = "Custom Plot"


class PlotDescriptor(HasStrictTraits):
    """ Plot description class to support TableEditor display of list of plots.
    """
    #: Id that's unique for a given plot among all created plots
    id = Str

    #: Should the plot be visible or hidden?
    visible = Bool(True)

    #: What container to draw the plot in. If <0, let the canvas manager decide
    # Can be set to "delete" to trigger a removal from the containing
    # PlotManager.
    container_idx = Any

    #: Filter expression applied to the source_data to build this plot
    data_filter = Str

    #: Actual plot being displayed
    plot = Instance(BasePlotContainer)

    #: Configurator the plot was built from
    plot_config = Instance(BasePlotConfigurator)

    #: Factory the plot was built with.
    plot_factory = Instance(BasePlotFactory)

    #: Type of plot
    plot_type = Enum(PLOT_TYPES + [CMAP_SCATTER_PLOT_TYPE, CUSTOM_PLOT_TYPE])

    #: Title of the plot
    plot_title = Str

    #: Name of the DF column displayed along the x axis
    x_col_name = Str

    #: Name of the DF column displayed along the y axis
    y_col_name = Str

    #: Name of the DF column displayed along the z axis
    z_col_name = Str

    #: Title displayed along the x axis
    x_axis_title = Str

    #: Title displayed along the y axis
    y_axis_title = Str

    #: Title displayed along the secondary y axis
    secondary_y_axis_title = Str

    #: Title displayed along the z axis
    z_axis_title = Str

    #: Whether the plot should update on data_source change
    frozen = Bool

    #: Launch the config editor
    edit_plot_style = Button("Edit")

    #: Event triggered if the plot's styling is changed and plot needs updating
    style_edited = Event

    @classmethod
    def from_config(cls, config):
        return cls(plot_config=config)

    # Traits listeners --------------------------------------------------------

    def _edit_plot_style_fired(self):
        ui = self.plot_config.plot_style.edit_traits(kind="livemodal")
        if ui.result:
            self.style_edited = True

    # Keep self and the contained configurator sync-ed

    def _plot_title_changed(self, new):
        if self.plot_config:
            self.plot_config.plot_title = new

    def _x_axis_title_changed(self, new):
        if self.plot_config:
            self.plot_config.x_axis_title = new

    def _y_axis_title_changed(self, new):
        if self.plot_config:
            self.plot_config.y_axis_title = new

    def _z_axis_title_changed(self, new):
        if self.plot_config:
            self.plot_config.z_axis_title = new

    def _plot_config_changed(self, new):
        self.plot_title = new.plot_title
        self.x_col_name = new.x_col_name
        self.x_axis_title = new.x_axis_title
        self.y_col_name = new.y_col_name
        self.y_axis_title = new.y_axis_title
        self.z_col_name = new.z_col_name
        self.z_axis_title = new.z_axis_title

    # Traits initialization methods -------------------------------------------

    def _plot_title_default(self):
        if self.plot_config:
            return self.plot_config.plot_title
        return ""

    def _x_col_name_default(self):
        if self.plot_config:
            return self.plot_config.x_col_name
        return ""

    def _y_col_name_default(self):
        if self.plot_config:
            return self.plot_config.y_col_name
        return ""

    def _z_col_name_default(self):
        if self.plot_config:
            return self.plot_config.z_col_name
        return ""

    def _x_axis_title_default(self):
        return self.x_col_name

    def _y_axis_title_default(self):
        return self.y_col_name

    def _z_axis_title_default(self):
        return self.z_col_name

    def _container_idx_default(self):
        return -1
