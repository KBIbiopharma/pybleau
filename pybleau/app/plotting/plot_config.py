""" Module containing plot configurator objects. They are responsible for
holding/collecting all data (arrays and styling info) to make a Chaco plot.

They display data and styling choices using TraitsUI views, and use user
selections to collect all necessary data from a source DataFrame. This is where
the translation between dataFrame and numpy arrays consumed by Chaco is done.
"""
import logging

import pandas as pd
from traits.api import Any, Bool, cached_property, Constant, Dict, \
    HasStrictTraits, Instance, Int, List, on_trait_change, Property, Str
from traitsui.api import CheckListEditor, EnumEditor, HGroup, InstanceEditor, \
    Item, Label, ListStrEditor, OKCancelButtons, Spring, Tabbed, VGroup, View

from pybleau.app.model.dataframe_analyzer import CATEGORICAL_COL_TYPES
from pybleau.app.plotting.bar_plot_style import BarPlotStyle
from pybleau.app.plotting.heatmap_plot_style import HeatmapPlotStyle
from pybleau.app.plotting.histogram_plot_style import HistogramPlotStyle
from pybleau.app.plotting.plot_style import BaseColorXYPlotStyle, \
    BaseXYPlotStyle, SingleLinePlotStyle, SingleScatterPlotStyle
from pybleau.app.plotting.renderer_style import BarRendererStyle, \
    CmapScatterRendererStyle, LineRendererStyle, ScatterRendererStyle
from pybleau.app.utils.chaco_colors import assign_renderer_colors
from pybleau.app.utils.string_definitions import BAR_PLOT_TYPE, \
    CMAP_SCATTER_PLOT_TYPE, HEATMAP_PLOT_TYPE, HIST_PLOT_TYPE, \
    LINE_PLOT_TYPE, SCATTER_PLOT_TYPE

X_COL_NAME_LABEL = "Column to plot along X"

Y_COL_NAME_LABEL = "Column to plot along Y"

logger = logging.getLogger(__name__)


class BasePlotConfigurator(HasStrictTraits):
    """ Base class for configuring a plot or a group of plots.
    """
    #: Source DataFrame to extract the data to plot from
    data_source = Instance(pd.DataFrame)

    #: Transformed DataFrame if data transformation are needed before plotting
    transformed_data = Property

    #: Grouped plot style information
    plot_style = Instance(BaseXYPlotStyle)

    #: Title of the future plot, or plot pattern for MultiConfigurators
    plot_title = Str

    #: Class to use to create TraitsUI window to open controls
    view_klass = Any(View)

    _plot_type_item = Property

    # List of attributes to export to pass to the factory
    _dict_keys = List

    # List of columns in the data source DF columns
    _available_columns = Property(depends_on="data_source")

    # DF columns in the data source that are non-categorical
    _numerical_columns = Property(depends_on="data_source")

    # Traits methods ----------------------------------------------------------

    def traits_view(self):
        """ Break the view building in 2 sets to simplify sub-classing.
        """
        view = self.view_klass(
            Tabbed(
                VGroup(
                    self._plot_type_item,
                    Item("plot_title"),
                    *self._data_selection_items(),
                    show_border=True, label="Data Selection"
                ),
                VGroup(
                    Item("plot_style", editor=InstanceEditor(), style="custom",
                         show_label=False),
                    show_border=True, label="Plot Style"
                ),
            ),
            resizable=True,
            buttons=OKCancelButtons,
            title="Configure plot",
        )
        return view

    def _get__plot_type_item(self):
        return HGroup(
            Spring(),
            Item('plot_type', style="readonly"),
            Spring(),
        )

    # Public interface --------------------------------------------------------

    def to_dict(self):
        """ Export self to a description dict, to be fed to a PlotFactory.

        Raises
        ------
        ValueError
            If no data source is available.

        KeyError
            If a column is requested, but not available.
        """
        if self.transformed_data is None:
            msg = "A configurator must be provided the dataframe the column" \
                  " names are referring to."
            logger.exception(msg)
            raise ValueError(msg)

        out = {}
        known_cols = self.transformed_data.columns
        for key in self._dict_keys:
            if isinstance(key, str):
                val = out[key] = getattr(self, key)
                if key.endswith("col_name") and val and val not in known_cols:
                    msg = "Unknown column name requested: '{}'.".format(val)
                    logger.exception(msg)
                    raise KeyError(msg)
            else:
                name, target_name = key
                out[target_name] = getattr(self, name)

        out["plot_style"] = self.plot_style
        return out

    def df_column2array(self, col_name, df=None):
        """ Collect a DF column and convert to numpy array, including index.
        """
        if df is None:
            df = self.transformed_data

        if col_name in ["index", df.index.name]:
            return df.index.values

        return df[col_name].values

    # Traits property getters/setters -----------------------------------------

    def _get_transformed_data(self):
        return self.data_source

    def _get__available_columns(self):
        index_name = self.data_source.index.name
        if index_name is None:
            index_name = "index"
        return list(self.data_source.columns) + [index_name]

    def _get__numerical_columns(self):
        cat_types = CATEGORICAL_COL_TYPES
        num_cols = self.data_source.select_dtypes(exclude=cat_types).columns
        index_name = self.data_source.index.name
        if index_name is None:
            index_name = "index"
        return list(num_cols) + [index_name]


class BaseSinglePlotConfigurator(BasePlotConfigurator):
    """ Configuration for a single plot.
    """
    #: Type of plot generated
    plot_type = Str

    #: Template that the plot is made from (if exists)
    source_template = Str

    #: Column name to display along the x-axis
    x_col_name = Str

    #: Column name to display along the y-axis
    y_col_name = Str

    #: Column name to display along the z-axis
    z_col_name = Str

    #: Title to display along the x-axis
    x_axis_title = Str

    #: Title to display along the y-axis
    y_axis_title = Str

    #: Column name(s) to display along the secondary y-axis
    second_y_col_name = Str

    #: Title to display along the secondary y-axis
    second_y_axis_title = Str

    #: Title to display along the z-axis
    z_axis_title = Str

    #: List of columns to display in an overlay on hover
    hover_col_names = List(Str)

    #: Data to be displayed on hover
    hover_data = Property(Dict)

    # Traits listeners --------------------------------------------------------

    def _x_col_name_changed(self, new):
        self.x_axis_title = col_name_to_title(new)

    def _y_col_name_changed(self, new):
        self.y_axis_title = col_name_to_title(new)

    def _z_col_name_changed(self, new):
        self.z_axis_title = col_name_to_title(new)

    # Traits property getters/setters -----------------------------------------

    def _get_hover_data(self):
        return {}

    # Traits initializers -----------------------------------------------------

    def _x_axis_title_default(self):
        return col_name_to_title(self.x_col_name)

    def _y_axis_title_default(self):
        return col_name_to_title(self.y_col_name)

    def _z_axis_title_default(self):
        return col_name_to_title(self.y_col_name)


class BaseSingleXYPlotConfigurator(BaseSinglePlotConfigurator):
    """ GUI configurator to create a new Chaco Plot.

    Note: may contain multiple renderers.
    """
    #: X coordinates of the data points
    x_arr = Property

    #: Y coordinates of the data points
    y_arr = Property

    #: Z (color) coordinates of the data points to generate colored renderers
    z_arr = Property

    #: Force floating point or integer column to be treated as discrete values?
    force_discrete_colors = Bool

    #: Supports hovering to display more data?
    _support_hover = Bool

    #: Whether this configuration will lead to 1 or multiple renderers
    _single_renderer = Property(Bool)

    plot_style = Instance(BaseXYPlotStyle)

    #: Whether the column selected to colorize the renderers contains floats
    colorize_by_float = Property(Bool,
                                 depends_on="transformed_data, z_col_name, "
                                            "force_discrete_colors")

    #: Flag setting whether to use only numerical columns in x/y selections
    _numerical_only = Bool

    @cached_property
    def _get_colorize_by_float(self):
        if not self.z_col_name:
            return False

        if self.transformed_data is None:
            # Skip for now: can't compute that property
            return False

        df = self.transformed_data
        color_by_discrete = (self.force_discrete_colors or
                             df[self.z_col_name].dtype in [bool, object])
        return not color_by_discrete

    # Traits property getters/setters -----------------------------------------

    def _get_x_arr(self):
        """ Collect the x array from the dataframe and the column name for x.

        Returns
        -------
        np.array or dict
            Collect either an array to display along the x axis or a dictionary
            of arrays mapped to z-values if a coloring column was selected.
        """
        if not self.x_col_name:
            return None

        if self._single_renderer:
            return self.df_column2array(self.x_col_name)
        else:
            grpby = self.transformed_data.groupby(self.z_col_name)
            all_x_arr = {}
            for z_val, subdf in grpby:
                all_x_arr[z_val] = self.df_column2array(self.x_col_name,
                                                        df=subdf)

            return all_x_arr

    def _get_y_arr(self):
        """ Collect the y array from the dataframe and the column name for y.

        Returns
        -------
        np.array or dict
            Collect either an array to display along the y axis or a dictionary
            of arrays mapped to z-values if a coloring column was selected.
        """
        if not self.y_col_name:
            return None

        if self._single_renderer:
            return self.df_column2array(self.y_col_name)
        else:
            grpby = self.transformed_data.groupby(self.z_col_name)
            all_y_arr = {}
            for z_val, subdf in grpby:
                all_y_arr[z_val] = self.df_column2array(self.y_col_name,
                                                        df=subdf)
            return all_y_arr

    def _get_hover_data(self):
        """ Collect additional arrays to store in the future ArrayPlotData to
        display on hover.

        Returns
        -------
        dict(str: np.array) or dict(str: dict)
            Map column names to arrays or to dictionaries mapping hue values to
            arrays if a coloring column was selected.
        """
        if not self.hover_col_names:
            return {}

        hover_data = {}
        if self._single_renderer:
            # No coloring of the scatter points: hover_data will contain arrays
            # for each of the properties to display.
            for col in self.hover_col_names:
                hover_data[col] = self.df_column2array(col)
        else:
            for col in self.hover_col_names:
                hover_data[col] = {}
                grpby = self.transformed_data.groupby(self.z_col_name)
                for z_val, subdf in grpby:
                    hover_data[col][z_val] = self.df_column2array(col,
                                                                  df=subdf)
        return hover_data

    def _get__single_renderer(self):
        if not self.z_col_name:
            # No coloring, so single renderer
            return True

        if self.transformed_data[self.z_col_name].dtype in [bool, object]:
            # Coloring by a string column so multiple renderers
            return False
        else:
            # Coloring by a numerical column so single renderer, unless
            # numerical values are forced to be treated as discrete values:
            return not self.force_discrete_colors

    def _get_z_arr(self):
        return None

    # Traits private interface ------------------------------------------------

    def _data_selection_columns(self):
        return self._numerical_columns if self._numerical_only else \
            self._available_columns

    def _color_selection_columns(self):
        return [""] + self._available_columns

    def _data_selection_items(self):
        """ Build the default list of items to select data to plot in XY plots.
        """
        columns = self._data_selection_columns()
        enum_data_columns = EnumEditor(values=columns)
        col_list_empty_option = self._color_selection_columns()
        optional_enum_data_columns = EnumEditor(values=col_list_empty_option)

        items = [
            HGroup(
                Item("x_col_name", editor=enum_data_columns,
                     label=X_COL_NAME_LABEL),
                Item("x_axis_title")
            ),
            HGroup(
                Item("y_col_name", editor=enum_data_columns,
                     label=Y_COL_NAME_LABEL),
                Item("y_axis_title")
            ),
            VGroup(
                HGroup(
                    Item("z_col_name", editor=optional_enum_data_columns,
                         label="Color column"),
                    Item("z_axis_title", label="Legend title",
                         visible_when="z_col_name"),
                    Item("force_discrete_colors",
                         tooltip="Treat floats as unrelated discrete "
                                 "values?",
                         visible_when="z_col_name")
                ),
                Item("_available_columns", label="Display on hover",
                     editor=ListStrEditor(selected="hover_col_names",
                                          multi_select=True),
                     visible_when="_support_hover"),
                show_border=True, label="Optional Data Selection"
            )
        ]
        return items

    # Traits initialization methods -------------------------------------------

    def __dict_keys_default(self):
        return ["plot_title", "x_col_name", "y_col_name", "z_col_name",
                "x_axis_title", "y_axis_title", "z_axis_title", "x_arr",
                "y_arr", "z_arr", "hover_data", "hover_col_names",
                "second_y_col_name", "second_y_axis_title"]


class BarPlotConfigurator(BaseSingleXYPlotConfigurator):
    """ Configuration object for building a bar plot.

    In default mode, a bar plot can display 2 columns as bars, using the
    content of the 2 columns as the x and y values to display. If the x values
    are not unique, y-values can be averaged. A color column can also be
    specified allowing multiple sets of bars to be drawn, one for each set of x
    values.

    Finally, x data may be encoded in the column names. For example, consider
    this "pivoted" table:
        male  female
    1    181    124
    2    183    114

    and imagine we want to draw a bar plot displaying the (average) weight per
    gender. In that case, the table must first be "melted" to build:
        weight  gender
    1      181    male
    2      183    male
    3      124  female
    4      114  female
    and then, it's possible to specify that we want to plot the weight as a
    function of gender.
    """
    #: Plot type
    plot_type = Str(BAR_PLOT_TYPE)

    #: Plot style
    plot_style = Instance(BarPlotStyle)

    #: Whether to "melt" (in the Pandas' sense) the DF to build the bar plot
    melt_source_data = Bool

    #: List of columns to melt to build the bar plot (1 bar per column)
    columns_to_melt = List

    #: View: number of column names to display in each column of checkbox
    column_len = Int(10)

    #: Transform DF to support melting multiple columns as individual bars
    transformed_data = Property(depends_on="data_source, columns_to_melt, "
                                           "z_col_name")

    renderer_style_klass = BarRendererStyle

    def __init__(self, **traits):
        # Consistency check:
        if "columns_to_melt" in traits and traits["columns_to_melt"]:
            traits["melt_source_data"] = True

        super(BarPlotConfigurator, self).__init__(**traits)

    def _data_selection_items(self):
        """ Add a melted mode to the default list of items.
        """
        default_items = super(BarPlotConfigurator, self)._data_selection_items()  # noqa
        # Since hover isn't supported in Bar plots, remove the view element to
        # avoid the window being too large (making it invisible isn't enough):
        default_items[-1].content.pop(-1)
        num_cols = 1 + len(self._available_columns) // self.column_len
        column_select_editor = CheckListEditor(values=self._available_columns,
                                               cols=num_cols)

        items = [
            VGroup(
                Item("melt_source_data", label="Multi-column mode"),
                VGroup(
                    HGroup(
                        Label("{}: selected column names".format(X_COL_NAME_LABEL)),  # noqa
                        Item("x_axis_title")
                    ),
                    HGroup(
                        Label("{}: selected column values".format(Y_COL_NAME_LABEL)),  # noqa
                        Item("y_axis_title")
                    ),
                    visible_when="melt_source_data"
                ),
                VGroup(
                    Item("columns_to_melt", label="Columns to plot",
                         editor=column_select_editor, style="custom"),
                    default_items[-1],  # hue control
                    visible_when="melt_source_data"
                ),
                VGroup(
                    *default_items,
                    visible_when="not melt_source_data"
                ),
                show_border=True
            )
        ]
        return items

    def _get_x_arr(self):
        if self.transformed_data is not self.data_source:
            self.x_col_name = "variable"

        return super(BarPlotConfigurator, self)._get_x_arr()

    def _get_y_arr(self):
        if self.transformed_data is not self.data_source:
            self.y_col_name = "value"

        return super(BarPlotConfigurator, self)._get_y_arr()

    @cached_property
    def _get_transformed_data(self):
        """ If in melt mode, melt the DF, otherwise, return the source_data.

        In melt mode, melt the columns to display as bars and keep the
        hue column as an ID variable (pandas terminology) so it can be used for
        splitting.
        """
        if self.data_source is None:
            return

        if self.columns_to_melt:
            if self.z_col_name:
                return self.data_source.melt(id_vars=[self.z_col_name],
                                             value_vars=self.columns_to_melt)
            else:
                return self.data_source.melt(value_vars=self.columns_to_melt)
        else:
            return self.data_source

    @on_trait_change("z_col_name, transformed_data", post_init=True)
    def update_style(self):
        # Only change the plot_style if we must since we will loose what was
        # already set:
        new_style = self._plot_style_default()
        style = self.plot_style
        change_needed = (
                new_style.__class__ != style.__class__ or
                len(new_style.renderer_styles) != len(style.renderer_styles) or
                any(r1.__class__ != r2.__class__ for r1, r2 in
                    zip(new_style.renderer_styles, style.renderer_styles))
        )
        if change_needed:
            self.plot_style = new_style

    def _plot_style_default(self):
        if not self.z_col_name:
            num_renderer = 1
        else:
            num_renderer = len(self.transformed_data[self.z_col_name].unique())

        renderer_styles = [self.renderer_style_klass()
                           for _ in range(num_renderer)]
        if num_renderer > 1:
            assign_renderer_colors(renderer_styles)

        return BarPlotStyle(renderer_styles=renderer_styles)

    # Traits initialization methods -------------------------------------------

    def __dict_keys_default(self):
        # Attributes to serialize to pass to factory or serialization for file
        # storage (serialization code adds plot_style to the list):
        return ["plot_title", "x_col_name", "y_col_name", "z_col_name",
                "x_axis_title", "y_axis_title", "z_axis_title", "x_arr",
                "y_arr", "z_arr", "hover_data", "hover_col_names",
                ("columns_to_melt", "x_labels")]


class LinePlotConfigurator(BaseSingleXYPlotConfigurator):
    """ Configuration object for building a plot with a single line renderer.

    See also
    --------
    `MultiLinePlotConfigurator` from pybleau.app.plotting.multi_plot_config.
    """
    plot_type = Str(LINE_PLOT_TYPE)

    plot_style = Instance(SingleLinePlotStyle, ())

    renderer_style_klass = LineRendererStyle

    _numerical_only = Bool(True)


class ScatterPlotConfigurator(BaseSingleXYPlotConfigurator):
    """ Configuration object for building scatter plot (std or color-mapped).
    """
    plot_type = Property(Str, depends_on="colorize_by_float")

    _support_hover = Bool(True)

    renderer_style_klass = Property(Any, depends_on="plot_type")

    _numerical_only = Bool(True)

    # Traits property getters/setters -----------------------------------------

    @cached_property
    def _get_plot_type(self):
        if self.colorize_by_float:
            return CMAP_SCATTER_PLOT_TYPE
        else:
            return SCATTER_PLOT_TYPE

    def _get_z_arr(self):
        # Collect an array for z (color) if the dimension exists and is
        # numerical
        if self.plot_type == CMAP_SCATTER_PLOT_TYPE:
            return self.data_source[self.z_col_name].values

    @cached_property
    def _get_renderer_style_klass(self):
        if self.plot_type == CMAP_SCATTER_PLOT_TYPE:
            return CmapScatterRendererStyle
        else:
            return ScatterRendererStyle

    @on_trait_change("data_source, z_col_name, plot_type", post_init=True)
    def update_style(self):
        new_style = self._plot_style_default()
        # Only change the plot_style if we must since we will lose what was
        # already set:
        style = self.plot_style
        change_needed = (
                new_style.__class__ != style.__class__ or
                len(new_style.renderer_styles) != len(style.renderer_styles) or
                any(r1.__class__ != r2.__class__ for r1, r2 in
                    zip(new_style.renderer_styles, style.renderer_styles))
        )
        if change_needed:
            self.plot_style = new_style

    # Traits initialization methods -------------------------------------------

    def _plot_style_default(self):
        if not self.z_col_name or self.plot_type == CMAP_SCATTER_PLOT_TYPE:
            num_renderer = 1
        else:
            num_renderer = len(self.data_source[self.z_col_name].unique())

        # Always use a color styler to support cmap scatters and multi-scatters
        renderer_styles = [self.renderer_style_klass()
                           for _ in range(num_renderer)]
        if num_renderer > 1:
            assign_renderer_colors(renderer_styles)

        style = BaseColorXYPlotStyle(
            colorize_by_float=self.colorize_by_float,
            renderer_styles=renderer_styles
        )
        if self.colorize_by_float:
            style.container_style.include_colorbar = True
        return style


class HistogramPlotConfigurator(BaseSingleXYPlotConfigurator):
    """ Configurator to define a histogram of single column, shown as bar plot.
    """
    plot_type = Constant(HIST_PLOT_TYPE)

    plot_style = Instance(HistogramPlotStyle, ())

    _dict_keys = ["plot_title", "x_col_name", "x_axis_title", "x_arr"]

    def _data_selection_items(self):
        """ This version doesn't need to expose the y axis since it is
        computed.
        """
        enum_data_columns = EnumEditor(values=self._numerical_columns)
        items = [
            HGroup(
                Item("x_col_name", editor=enum_data_columns,
                     label="Column to plot along X"),
                Item("x_axis_title")
            )
        ]
        return items


class HeatmapPlotConfigurator(BaseSingleXYPlotConfigurator):
    """ Configuration object for building a plot with 2D heatmap renderer.
    """
    plot_type = Constant(HEATMAP_PLOT_TYPE)

    plot_style = Instance(HeatmapPlotStyle)

    def _data_selection_items(self):
        enum_data_columns = EnumEditor(values=self._available_columns)
        num_only_columns = EnumEditor(values=self._numerical_columns)
        items = [
            HGroup(
                    Item("x_col_name", editor=num_only_columns,
                         label="Column to plot along X"),
                    Item("x_axis_title")
                ),
            HGroup(
                Item("y_col_name", editor=num_only_columns,
                     label="Column to plot along Y"),
                Item("y_axis_title")
            ),
            HGroup(
                Item("z_col_name", editor=enum_data_columns,
                     label="Color column"),
                Item("z_axis_title")
            ),
        ]
        return items

    def _get_z_arr(self):
        return self.data_source.pivot_table(index=self.y_col_name,
                                            columns=self.x_col_name,
                                            values=self.z_col_name).values

    def _plot_style_default(self):
        style = HeatmapPlotStyle()
        style.container_style.include_colorbar = True
        return style


def col_name_to_title(col_name):
    return col_name.replace("_", " ")


DEFAULT_CONFIGS = {HIST_PLOT_TYPE: HistogramPlotConfigurator,
                   BAR_PLOT_TYPE: BarPlotConfigurator,
                   LINE_PLOT_TYPE: LinePlotConfigurator,
                   SCATTER_PLOT_TYPE: ScatterPlotConfigurator,
                   CMAP_SCATTER_PLOT_TYPE: ScatterPlotConfigurator,
                   HEATMAP_PLOT_TYPE: HeatmapPlotConfigurator}

DEFAULT_STYLES = {HIST_PLOT_TYPE: HistogramPlotStyle,
                  BAR_PLOT_TYPE: BarPlotStyle,
                  LINE_PLOT_TYPE: SingleLinePlotStyle,
                  SCATTER_PLOT_TYPE: SingleScatterPlotStyle,
                  CMAP_SCATTER_PLOT_TYPE: SingleScatterPlotStyle,
                  HEATMAP_PLOT_TYPE: HeatmapPlotStyle}
