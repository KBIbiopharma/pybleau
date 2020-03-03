""" Module containing multi-plot configurator objects. They are responsible for
holding/collecting all data (arrays and styling info) to make multiple Chaco
plots easily (as opposed to Plots holding multiple renderers).

They display data and styling choices using TraitsUI views, and use user
selections to collect all necessary data from a source DataFrame. This is where
the translation between dataFrame and numpy arrays consumed by Chaco is done.
"""
import logging

from traits.api import Bool, Constant, Enum, List, Str
from traitsui.api import CheckListEditor, EnumEditor, HGroup, Item, VGroup

from .plot_config import BasePlotConfigurator, HistogramPlotConfigurator, \
    HistogramPlotStyle, LinePlotConfigurator, SingleLinePlotStyle, \
    X_COL_NAME_LABEL
from .plot_style import BaseColorXYPlotStyle, LineRendererStyle
from ..utils.string_definitions import MULTI_HIST_PLOT_TYPE, \
    MULTI_LINE_PLOT_TYPE
from .plot_config import BaseSingleXYPlotConfigurator

logger = logging.getLogger(__name__)

Y_COL_NAME_LABEL = "Columns to plot along Y"

SINGLE_CURVE = "Multi single-curve plots"

MULTI_CURVE = "Single multi-curve plot"


class BaseMultiPlotConfigurator(BasePlotConfigurator):

    #: Checkbox to support plotting all columns
    select_all = Bool

    def to_config_list(self):
        raise NotImplementedError()


class MultiLinePlotConfigurator(BaseSingleXYPlotConfigurator,
                                BaseMultiPlotConfigurator):
    """ Configurator to create multiple single-line plots or a single
    multi-line plot.
    """
    #: Type of the series of plots being created
    plot_type = Constant(MULTI_LINE_PLOT_TYPE)

    #: Column name to display along the x-axis
    x_col_name = Str

    #: Title to display along the x-axis
    x_axis_title = Str

    #: List of column names to plot against x_col_name
    y_col_names = List(Str)

    #: Will lead to a multi-renderer plot or multiple single-renderer plots
    multi_mode = Enum([SINGLE_CURVE, MULTI_CURVE])

    # Traits methods ----------------------------------------------------------

    def _data_selection_items(self):
        """ Build the default list of items to select data to plot in XY plots.
        """
        enum_data_columns = EnumEditor(values=self._available_columns)
        num_cols = 1 + len(self._available_columns) // 10
        data_columns_selector = CheckListEditor(values=self._available_columns,
                                                cols=num_cols)

        items = [
            Item("multi_mode"),
            HGroup(
                Item("x_col_name", editor=enum_data_columns,
                     label=X_COL_NAME_LABEL),
                Item("x_axis_title")
            ),
            HGroup(
                VGroup(
                    Item("y_col_names", editor=data_columns_selector,
                         label=Y_COL_NAME_LABEL, style="custom"),
                    Item("select_all", label="(Un)select all"),
                ),
            ),
        ]
        return items

    def _select_all_changed(self, new):
        if new:
            self.y_col_names = self._available_columns
        else:
            self.y_col_names = []

    def to_config_list(self):
        """ Generate the list of configurators from user selection.

        Converts self into multiple line configurators (in single-curve mode)
        or prepare for the generation of a multi-curve plot (in single-plot
        mode).
        """
        config_list = []
        if self.multi_mode == SINGLE_CURVE:
            for y_col in self.y_col_names:
                single_plot_config = LinePlotConfigurator(
                    data_source=self.data_source,
                    plot_title=self.plot_title,
                    x_col_name=self.x_col_name,
                    x_axis_title=self.x_col_name,
                    y_col_name=y_col,
                    y_axis_title=y_col,
                    plot_style=SingleLinePlotStyle()
                )
                config_list.append(single_plot_config)
        else:
            renderer_styles = [LineRendererStyle() for _ in self.y_col_names]
            self.plot_style = BaseColorXYPlotStyle(
                renderer_styles=renderer_styles,
                colorize_by_float=False
            )
            config_list = [self]

        return config_list

    def _get_x_arr(self):
        """ Collect the x array from the dataframe and the column name for x.

        Returns
        -------
        np.array or dict
            Collect either an array to display along the x axis or a dictionary
            of arrays mapped to z-values if a coloring column was selected.
        """
        all_y_arr = {}
        for y_val in self.y_col_names:
            all_y_arr[y_val] = self.df_column2array(self.x_col_name)
        return all_y_arr

    def _get_y_arr(self):
        """ Collect the y array from the dataframe and the column name for y.

        Returns
        -------
        np.array or dict
            Collect either an array to display along the y axis or a dictionary
            of arrays mapped to z-values if a coloring column was selected.
        """
        all_y_arr = {}
        for y_val in self.y_col_names:
            all_y_arr[y_val] = self.df_column2array(y_val)
        return all_y_arr


class MultiHistogramPlotConfigurator(BaseMultiPlotConfigurator):
    """ Configurator to create multiple histograms.
    """
    #: Type of the series of plots being created
    plot_type = Constant(MULTI_HIST_PLOT_TYPE)

    #: List of col names to make a histogram of
    x_col_names = List(Str)

    def _data_selection_items(self):
        """ Build the default list of items to select data to plot in XY plots.
        """
        num_cols = 1 + len(self._available_columns) // 10
        data_columns_selector = CheckListEditor(values=self._available_columns,
                                                cols=num_cols)
        items = [
            Item("x_col_names", editor=data_columns_selector,
                 label="Datasets", style="custom"),
            Item("select_all", label="(Un)select all"),
        ]
        return items

    def _select_all_changed(self, new):
        if new:
            self.x_col_names = self._available_columns
        else:
            self.x_col_names = []

    def to_config_list(self):
        """ Convert self into multiple Histogram configurators.
        """
        config_list = []
        for x_col in self.x_col_names:
            single_plot_config = HistogramPlotConfigurator(
                data_source=self.data_source,
                plot_title=self.plot_title,
                x_col_name=x_col,
                x_axis_title=x_col,
                plot_style=HistogramPlotStyle()
            )
            config_list.append(single_plot_config)
        return config_list
