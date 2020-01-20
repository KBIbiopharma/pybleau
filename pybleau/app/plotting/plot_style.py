
from traits.api import Any, Bool, Button, Dict, Enum, Float, HasStrictTraits, \
    Int, List, Property, Range, Trait, Tuple
from traitsui.api import EnumEditor, HGroup, Item, OKCancelButtons, \
    RangeEditor, VGroup, View
from enable.api import ColorTrait, LineStyle
from enable.markers import MarkerNameDict, marker_names
from kiva.trait_defs.kiva_font_trait import font_families
from ..utils.chaco_colors import ALL_CHACO_PALETTES, ALL_MPL_PALETTES

DEFAULT_AXIS_LABEL_FONT_SIZE = 18

DEFAULT_TITLE_FONT_SIZE = 18

DEFAULT_TITLE_FONT = "modern"

DEFAULT_MARKER_SIZE = 6

DEFAULT_LINE_WIDTH = 1.3

DEFAULT_NUM_BINS = 10

DEFAULT_COLOR = "blue"

SPECIFIC_CONFIG_CONTROL_LABEL = "Specific controls"

DEFAULT_DIVERG_PALETTE = "hsv"

DEFAULT_CONTIN_PALETTE = "cool"

IGNORE_DATA_DUPLICATES = "ignore"


class BasePlotStyle(HasStrictTraits):
    """ Styling parameters for building Chaco renderers.

    These objects are designed to be Used by PlotFactories to generate a plot,
    but also embedded
    """
    #: Color of the renderer (ignore if more than 1)
    color = ColorTrait(DEFAULT_COLOR)

    #: Name of the palette to pick colors from in z direction
    color_palette = Enum(values="_all_palettes")

    #: List of available color palettes
    _all_palettes = List(ALL_MPL_PALETTES)

    #: Transparency of the renderer
    alpha = Range(value=1., low=0., high=1.)

    #: View elements for users to control these parameters
    general_view_elements = Property(List)

    #: Font used to draw the plot and axis titles
    title_font_name = Enum(DEFAULT_TITLE_FONT, values="_all_fonts")

    #: List of all available fonts
    _all_fonts = List

    #: Font size used to draw the plot title
    title_font_size = Int(DEFAULT_TITLE_FONT_SIZE)

    #: Font size used to draw the x axis title
    x_title_font_size = Int(DEFAULT_AXIS_LABEL_FONT_SIZE)

    #: Font size used to draw the y axis title
    y_title_font_size = Int(DEFAULT_AXIS_LABEL_FONT_SIZE)

    #: Font size used to draw the z axis title
    z_title_font_size = Int(DEFAULT_AXIS_LABEL_FONT_SIZE)

    #: Angle to rotate the X axis labels (string x values only)
    x_axis_label_rotation = Int

    #: Angle to rotate the Y axis labels (string x values only)
    y_axis_label_rotation = Int

    #: Whether to force display of all values along X axis or allow decimation
    # (ONLY USED with string labels)
    show_all_x_ticks = Bool

    #: Low value of the x-axis range
    x_axis_range_low = Float(-1)

    #: High value of the x-axis range
    x_axis_range_high = Float(-1)

    #: Low value of the y-axis range
    y_axis_range_low = Float(-1)

    #: High value of the y-axis range
    y_axis_range_high = Float(-1)

    #: Automatic low value of the x-axis range for plot full view
    auto_x_axis_range_low = Float(-1)

    #: High value of the x-axis range
    auto_x_axis_range_high = Float(-1)

    #: Low value of the y-axis range
    auto_y_axis_range_low = Float(-1)

    #: High value of the y-axis range
    auto_y_axis_range_high = Float(-1)

    #: Button to reset the x-axis range to automatic values
    reset_x_axis_range = Button("Reset")

    #: Button to reset lthe y-axis range to automatic values
    reset_y_axis_range = Button("Reset")

    #: Linear or log scale for the independent variable?
    index_scale = Enum("linear", "log")

    #: Linear or log scale for the dependent variable?
    value_scale = Enum("linear", "log")

    #: List of attribute names to export to dictionary
    dict_keys = List

    #: View klass. Override to customize the views, for example their icon
    view_klass = Any(default_value=View)

    #: Keywords passed to create the view
    view_kw = Dict

    def __all_fonts_default(self):
        return sorted(list(font_families.keys()))

    def to_dict(self):
        return {key: getattr(self, key) for key in self.dict_keys}

    def _dict_keys_default(self):
        return ["color", "color_palette", "alpha", "title_font_size",
                "x_title_font_size", "y_title_font_size", "z_title_font_size",
                "x_axis_label_rotation", "y_axis_label_rotation",
                "title_font_name", "index_scale", "value_scale",
                "x_axis_range_low", "x_axis_range_high", "y_axis_range_low",
                "y_axis_range_high", "show_all_x_ticks"]

    def _get_general_view_elements(self):
        elemens = (
            VGroup(
                VGroup(
                    VGroup(
                        HGroup(
                            Item("x_axis_range_low", label="X-axis range"),
                            Item("x_axis_range_high", show_label=False),
                            Item("reset_x_axis_range", show_label=False)
                        ),
                        HGroup(
                            Item("y_axis_range_low", label="Y-axis range"),
                            Item("y_axis_range_high", show_label=False),
                            Item("reset_y_axis_range", show_label=False)
                        ),
                        show_border=True, label="Range controls"
                    ),
                    HGroup(
                        Item("index_scale", label="X-axis scale"),
                        Item("value_scale", label="Y-axis scale"),
                        show_border=True, label="Scaling controls"
                    ),
                    show_border=True, label="Axis controls"
                ),
                VGroup(
                    HGroup(
                        Item('color', label="Color", style="custom"),
                        Item("color_palette"),
                    ),
                    Item('alpha', label="Transparency"),
                    show_border=True, label="Color controls"
                ),
                VGroup(
                    Item('title_font_name'),
                    HGroup(
                        Item('title_font_size',
                             editor=RangeEditor(low=9, high=32)),
                        Item('x_title_font_size',
                             editor=RangeEditor(low=9, high=32)),
                        Item('y_title_font_size',
                             editor=RangeEditor(low=9, high=32)),
                        Item('z_title_font_size',
                             editor=RangeEditor(low=9, high=32)),
                    ),
                    show_border=True, label="Title font controls",
                ),
                VGroup(
                    HGroup(
                        Item('x_axis_label_rotation',
                             editor=RangeEditor(low=0, high=360)),
                        Item('show_all_x_ticks',
                             label="Force all ticks/labels"),
                    ),
                    Item('y_axis_label_rotation',
                         editor=RangeEditor(low=0, high=360)),
                    show_border=True, label="Axis label controls (str only)",
                )
            ),
        )
        return elemens

    def traits_view(self):
        view = self.view_klass(*self.general_view_elements, **self.view_kw)
        return view

    def _reset_x_axis_range_changed(self):
        self.x_axis_range_low = self.auto_x_axis_range_low
        self.x_axis_range_high = self.auto_x_axis_range_high

    def _reset_y_axis_range_changed(self):
        self.y_axis_range_low = self.auto_y_axis_range_low
        self.y_axis_range_high = self.auto_y_axis_range_high

    def initialize_axis_ranges(self, plot, transform=None):
        """ Initialize the axis ranges from proviuded Plot or renderer.
        """
        if transform is None:
            def transform(x):
                return x
        elif isinstance(transform, int):
            ndigits = transform

            def transform(x):
                return round(x, ndigits)

        # Avoid UI polluting with non-sensical digits
        self.x_axis_range_low = transform(plot.x_axis.mapper.range.low)
        self.auto_x_axis_range_low = self.x_axis_range_low
        self.x_axis_range_high = transform(plot.x_axis.mapper.range.high)
        self.auto_x_axis_range_high = self.x_axis_range_high
        self.y_axis_range_low = transform(plot.y_axis.mapper.range.low)
        self.auto_y_axis_range_low = self.y_axis_range_low
        self.y_axis_range_high = transform(plot.y_axis.mapper.range.high)
        self.auto_y_axis_range_high = self.y_axis_range_high

    def _view_kw_default(self):
        return dict(
            resizable=True,
            buttons=OKCancelButtons,
            title="Plot Styling",
        )


class ScatterPlotStyle(BasePlotStyle):
    """ Styling object for customizing scatter plots.
    """
    #: The type of marker to use
    marker = Trait("circle", MarkerNameDict,
                   editor=EnumEditor(values=marker_names))

    #: The size of the marker
    marker_size = Int(DEFAULT_MARKER_SIZE)

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                VGroup(
                    Item('marker', label="Marker"),
                    Item('marker_size',
                         editor=RangeEditor(low=1, high=20)),
                    show_border=True, label=SPECIFIC_CONFIG_CONTROL_LABEL
                ),
                *self.general_view_elements
            ),
            ** self.view_kw
        )
        return view

    def _dict_keys_default(self):
        general_items = super(ScatterPlotStyle, self)._dict_keys_default()
        return general_items + ["marker", "marker_size"]


class BarPlotStyle(BasePlotStyle):
    """ Styling object for customizing line plots.
    """
    #: Width of each bar. Leave as 0 to have it computed programmatically.
    bar_width = Float

    #: How to handle multiple bars from hue dim? Next to each other or stacked?
    # Stacked bars aren't working right in current Chaco
    bar_style = Enum(["group"])  # , "stack"

    #: How to handle multiple values contributing to a single bar?
    data_duplicate = Enum(["mean", IGNORE_DATA_DUPLICATES])

    #: Whether to display error bars when multiple values contribute to a bar
    show_error_bars = Bool

    #: Whether to force display of all values along X axis or allow decimation
    # (ONLY USED with string labels)
    show_all_x_ticks = Bool(True)

    def traits_view(self):
        allow_errors = "data_duplicate != '{}'".format(IGNORE_DATA_DUPLICATES)

        view = self.view_klass(
            VGroup(
                VGroup(
                    HGroup(
                        Item('bar_width'),
                        Item('bar_style', tooltip="When multiple bars, display"
                                                  " side by side or stacked?")
                    ),
                    HGroup(
                        Item('data_duplicate'),
                        Item("show_error_bars", label="Show error bars?",
                             enabled_when=allow_errors)
                    ),
                    show_border=True, label=SPECIFIC_CONFIG_CONTROL_LABEL
                ),
                *self.general_view_elements
            ),
            **self.view_kw
        )
        return view

    def _dict_keys_default(self):
        general_items = super(BarPlotStyle, self)._dict_keys_default()
        return general_items + ["bar_width", "bar_style", "show_error_bars",
                                "data_duplicate"]


class LinePlotStyle(BasePlotStyle):
    """ Styling object for customizing line plots.
    """
    line_width = Float(DEFAULT_LINE_WIDTH)

    line_style = LineStyle("solid")

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                VGroup(
                    Item('line_width'),
                    Item('line_style', style="custom"),
                    show_border=True, label=SPECIFIC_CONFIG_CONTROL_LABEL
                ),
                *self.general_view_elements
            ),
            **self.view_kw
        )
        return view

    def _dict_keys_default(self):
        general_items = super(LinePlotStyle, self)._dict_keys_default()
        return general_items + ["line_width", "line_style"]


class HistogramPlotStyle(BasePlotStyle):
    """ Styling object for customizing histogram plots.
    """

    #: Number of bins: the bar width computed from that and the data range
    num_bins = Int(DEFAULT_NUM_BINS)

    #: bin start and end to use. Leave empty to use the data's min and max.
    bin_limits = Tuple

    #: Factor to apply to the default bar width. Set to 1 for bars to touch.
    bar_width_factor = Float(1.0)

    # Extra parameters not needed in the view ---------------------------------

    #: Meaning of the parameter above: data space or screen space?
    # Export but don't expose in the UI to make sure it is the data space since
    # the bar width computation makes that assumption.
    bar_width_type = Enum("data", "screen")

    def _dict_keys_default(self):
        general_items = super(HistogramPlotStyle, self)._dict_keys_default()
        return general_items + ["num_bins", "bin_limits", "bar_width_factor",
                                "bar_width_type"]

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                HGroup(
                    Item('num_bins', label="Number of bins"),
                    Item('bar_width_factor',
                         editor=RangeEditor(low=0.1, high=1.)),
                    show_border=True, label=SPECIFIC_CONFIG_CONTROL_LABEL
                ),
                *self.general_view_elements
            ),
            ** self.view_kw
        )
        return view


class HeatmapPlotStyle(BasePlotStyle):
    """
    """
    #: Number of bins: the bar width computed from that and the data range
    colormap_str = Enum(DEFAULT_CONTIN_PALETTE, values="_colormap_list")

    #:
    _colormap_list = List

    colorbar_low = Float

    colorbar_high = Float(1.0)

    interpolation = Enum("nearest", "bilinear", "bicubic")

    add_contours = Bool(False)

    contour_levels = Int(5)

    contour_styles = Enum("solid", "dash")

    contour_alpha = Float(0.9)

    contour_widths = Float(0.85)

    def _dict_keys_default(self):
        general_items = super(HeatmapPlotStyle, self)._dict_keys_default()
        return general_items + ["colormap_str", "colorbar_low",
                                "colorbar_high", "interpolation",
                                "add_contours", "contour_levels",
                                "contour_styles", "contour_alpha",
                                "contour_widths"]

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                VGroup(
                    HGroup(
                        Item("interpolation"),
                    ),
                    HGroup(
                        Item("add_contours"),
                        Item("contour_levels", label="Num. contours",
                             enabled_when="add_contours"),
                        Item("contour_styles", label="Contour line type",
                             enabled_when="add_contours"),
                        Item("contour_alpha",
                             editor=RangeEditor(low=0., high=1.),
                             label="Contour transparency",
                             enabled_when="add_contours"),
                        Item("contour_widths",
                             editor=RangeEditor(low=0.1, high=4.),
                             label="Contour widths",
                             enabled_when="add_contours"),
                        show_border=True,
                    ),
                    HGroup(
                        Item('colormap_str'),
                        Item('colorbar_low'),
                        Item('colorbar_high'),
                        show_border=True,
                    ),
                    show_border=True, label=SPECIFIC_CONFIG_CONTROL_LABEL
                ),
                *self.general_view_elements
            ),
            ** self.view_kw
        )
        return view

    def __colormap_list_default(self):
        return ALL_CHACO_PALETTES
