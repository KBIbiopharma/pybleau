""" Module containing multi-plot configurator objects. They are responsible for
holding/collecting all data (arrays and styling info) to make multiple Chaco
plots easily.

They display data and styling choices using TraitsUI views, and use user
selections to collect all necessary data from a source DataFrame. This is where
the translation between dataFrame and numpy arrays consumed by Chaco is done.
"""
import logging

from traits.api import Bool, Constant, Instance, List, Str
from traitsui.api import CheckListEditor, EnumEditor, HGroup, Item, VGroup

from .plot_config import BasePlotConfigurator, HistogramPlotConfigurator, \
    HistogramPlotStyle, LinePlotConfigurator, SingleLinePlotStyle, X_COL_NAME_LABEL

logger = logging.getLogger(__name__)

MULTI_HIST_PLOT_TYPE = "Multi-Histogram Plot(s)"

MULTI_LINE_PLOT_TYPE = "Multi-Line Plot(s)"

Y_COL_NAME_LABEL = "Columns to plot along Y"


class BaseMultiPlotConfigurator(BasePlotConfigurator):

    #: Checkbox to support plotting all columns
    select_all = Bool

    def to_config_list(self):
        raise NotImplementedError()


class MultiLinePlotConfigurator(BaseMultiPlotConfigurator):
    """ Configurator to create multiple histograms.
    """
    #: Type of the series of plots being created
    plot_type = Constant(MULTI_LINE_PLOT_TYPE)

    #: Styling of the plots created
    plot_style = Instance(SingleLinePlotStyle, ())

    #: Column name to display along the x-axis
    x_col_name = Str

    #: Title to display along the x-axis
    x_axis_title = Str

    #: List of column names to plot against x_col_name
    y_col_names = List(Str)

    # Traits methods ----------------------------------------------------------

    def _data_selection_items(self):
        """ Build the default list of items to select data to plot in XY plots.
        """
        enum_data_columns = EnumEditor(values=self._available_columns)
        num_cols = 1 + len(self._available_columns) // 10
        data_columns_selector = CheckListEditor(values=self._available_columns,
                                                cols=num_cols)

        items = [
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
        """ Convert self into multiple Histogram configurators.

        FIXME: This makes all plots have the same style instance, which can be
         bad.
        """
        config_list = []
        for y_col in self.y_col_names:
            single_plot_config = LinePlotConfigurator(
                data_source=self.data_source,
                plot_title=self.plot_title,
                x_col_name=self.x_col_name,
                x_axis_title=self.x_col_name,
                y_col_name=y_col,
                y_axis_title=y_col,
                plot_style=self.plot_style
            )
            config_list.append(single_plot_config)
        return config_list


class MultiHistogramPlotConfigurator(BaseMultiPlotConfigurator):
    """ Configurator to create multiple histograms.
    """
    #: Type of the series of plots being created
    plot_type = Constant(MULTI_HIST_PLOT_TYPE)

    #: Styling of the plots created
    plot_style = Instance(HistogramPlotStyle, ())

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

        FIXME: This makes all plots have the same style instance, which can be
         bad.
        """
        config_list = []
        for x_col in self.x_col_names:
            single_plot_config = HistogramPlotConfigurator(
                data_source=self.data_source,
                plot_title=self.plot_title,
                x_col_name=x_col,
                x_axis_title=x_col,
                plot_style=self.plot_style
            )
            config_list.append(single_plot_config)
        return config_list
