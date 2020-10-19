import logging
from pandas import concat, DataFrame
import numpy as np
from functools import partial

from traits.api import Bool, cached_property, Callable, Dict, Enum, Event, \
    Instance, Int, List, observe, on_trait_change, Property, Str

from app_common.std_lib.str_utils import add_suffix_if_exists, sanitize_string
from app_common.model_tools.data_element import DataElement

from ..tools.filter_expression_manager import FilterExpression
try:
    from .dataframe_plot_manager import DataFramePlotManager
except ImportError:
    DataFramePlotManager = object

logger = logging.getLogger(__name__)

DEFAULT_SUMMARY_ELEMENTS = [
    u'count', u'mean', u'std', u'min', u'25%', u'50%', u'75%', u'max'
]

DEFAULT_CATEG_SUMMARY_ELEMENTS = ['count', 'unique', 'top', 'freq', 'next',
                                  'next_freq']

REVERSED_SUFFIX = " (REVERSED)"

NO_SORTING_ENTRY = ""

CATEGORICAL_COL_TYPES = ['O', 'category', 'datetime64']


class InvalidQuery(ValueError):
    pass


class DataFrameAnalyzer(DataElement):
    """ Tool that filters data from and builds a customizable summary of a DF.

    NOTE: the source dataframe is copied because its column names may be
    changed so that the filtering tool may be used (requires column names to be
    valid variable name).

    TODO: This class copies the source_df which could lead to large amount of
    memory wasted if the DF is large. Is there a way to avoid that copy?
    """

    # Data storage attributes -------------------------------------------------

    #: **Copy** of the data to analyze, where column names have been sanitized
    source_df = Instance(DataFrame)

    #: Custom notes describing the columns of the source_df
    column_descr = Dict

    #: Result of filtering the source_df with the filter_exp expression
    filtered_df = Instance(DataFrame)

    #: Subset of filtered_df being displayed
    displayed_df = Instance(DataFrame)

    #: Length of filtered_df to display. Set to -1 to display all.
    num_displayed_rows = Int(500)

    #: Number of rows to add to displayed_df if smaller than filtered_df
    num_display_increment = Int

    # Transformation attributes -----------------------------------------------

    #: Expression to apply to filter data
    filter_exp = Str

    #: Function to apply to the filter_exp before passing to the DF
    filter_transformation = Callable

    #: Whether to auto-recompute filtered DF when filter_exp changes
    filter_auto_apply = Bool(True)

    #: List of known filter expressions (mapped to a unique name)
    known_filter_exps = List(FilterExpression)

    #: Result of the summary statistics analysis (floating point columns)
    summary_df = Instance(DataFrame)

    #: List of analysis elements we need
    summary_index = List(DEFAULT_SUMMARY_ELEMENTS)

    #: Result of the summary statistics analysis (floating point columns)
    summary_categorical_df = Instance(DataFrame)

    #: Behavior when a filter leads to an exception. Mostly useful for testing
    filter_error_handling = Enum(["raise", "warn", "ignore"])

    #: Name of the column to sort the table on
    sort_by_col = Enum(values='sort_by_col_list')

    #: List of possible values for the sort_by_col
    sort_by_col_list = Property(List, depends_on="source_df")

    #: Whether the source data's index is sorted
    data_sorted = Bool

    #: Name of the index if any
    index_name = Property(Str, depends_on="source_df")

    #: List of DF row locations currently selected. Used by PlotManager and
    #: TableEditor, but not invariant under sorting operations.
    selected_idx = List(Int)

    #: List of DF index values that are selected
    data_selected = List

    #: Restrict displayed_df to the selected data
    show_selected_only = Bool

    #: All plotting managers created, to sync selection and source_data
    plot_manager_list = List(DataFramePlotManager)

    #: Event triggered when all plotters are sync-ed with self.selected_idx
    selected_data_in_plotter_updated = Event

    #: List of types to display information in the categorical summary rather
    # than numerical summary:
    categorical_dtypes = List(CATEGORICAL_COL_TYPES)

    def __init__(self, convert_source_dtypes=False, data_sorted=True,
                 **traits):

        traits["data_sorted"] = data_sorted
        source_df = traits.get("source_df", None)
        if isinstance(source_df, DataFrame):
            # If the index isn't unique, selection functionalities will break.
            index = source_df.index
            if len(index.unique()) != len(index):
                # The breakage will come from the fact that the translation
                # between a selection position to a selected index isn't
                # bijective:
                msg = "The index of the source DataFrame isn't unique. Some " \
                      "selection functionality will break. The DF must be " \
                      "modified"
                logger.exception(msg)
                raise NotImplementedError(msg)

            traits["source_df"] = copy_and_sanitize(
                source_df, convert_dtypes=convert_source_dtypes,
                sort_index=data_sorted
            )
        else:
            msg = "Creating a {} without the source dataframe. Most " \
                  "functionality will break until that attribute is set."
            msg = msg.format(self.__class__.__name__)
            logger.warning(msg)

        # Pop out a few traits, to ensure they are assigned in the right order
        # and trigger the right listeners:
        sort_by = traits.pop("sort_by_col", None)
        data_selected = traits.pop("data_selected", None)

        super(DataFrameAnalyzer, self).__init__(**traits)

        if self.source_df is not None:
            self.compute_summary()
            self.compute_categorical_summary()

        if sort_by:
            self.sort_by_col = sort_by

        # Make sure the data_selected is set after the filtered data is
        # computed, so row index is computed correctly:
        # FIXME: for now, creating the analyzer with data selection isn't
        # reflected in the UI.
        if data_selected:
            self.data_selected = data_selected

    def map_idx_to_df_index(self, idx_list):
        """ Maps a list of positions along the DF to a list of filtered_df
        index values which remain unchanged even when filter or sort_by change.
        """
        # We use the filtered df instead of the displayed_df because plots
        # display all filtered data and may be the source of the selection:
        return self.filtered_df.index[idx_list].tolist()

    def map_df_index_to_idx(self, index_vals):
        """ Maps a list of index values to a list of positions along the DF.

        Note: this call looses the order of index_vals because of isin. isin is
        used to avoid for loops, as selection may contain a lot of values.
        """
        return list(np.where(self.filtered_df.index.isin(index_vals))[0])

    def recompute_filtered_df(self):
        """ Force a recomputation of the filtered DF from the source one.
        """
        self.filtered_df = self._compute_filtered_df()

    def shuffle_filtered_df(self):
        """ Shuffle the filtered DF order randomly.
        """
        self.sort_by_col = NO_SORTING_ENTRY
        self.filtered_df = self.filtered_df.sample(frac=1)

    # Traits Listeners --------------------------------------------------------

    @observe("column_descr:items")
    def check_col_descr_change(self, event):
        for key, value in event.added.items():
            if key not in self.source_df.columns:
                msg = f"Note added for invalid column {key}. Removing it... " \
                    f"(Note was: {value})"
                logger.error(msg)
                self.column_descr.pop(key)

    @on_trait_change("plot_manager_list.index_selected[]", post_init=True)
    def update_selected_idx(self, object, name, old, new):
        """ Selection modified in plot tools: update table selections.
        """
        new = object.index_selected
        if set(self.selected_idx) != set(new):
            self.selected_idx = new

    @on_trait_change("selected_idx[]", post_init=True)
    def update_selected_idx_in_plotter(self):
        """ Update selection in all plot managers if selection changed in table
        """
        for plot_manager in self.plot_manager_list:
            current = plot_manager.index_selected
            if set(current) != set(self.selected_idx):
                plot_manager.index_selected = self.selected_idx

        self.selected_data_in_plotter_updated = True

    @on_trait_change("selected_idx[]", post_init=True)
    def update_data_selected(self):
        """ Update the selection in terms of the DF index values, which remains
        unmodified even when changing the way the data is sorted.
        """
        # Store the selection in terms of the DF index
        data_selected = self.map_idx_to_df_index(self.selected_idx)
        if set(self.data_selected) != set(data_selected):
            self.data_selected = data_selected

    @on_trait_change("data_selected")
    def update_selected_idx_from_data(self):
        """ Update selected table rows from DF index.
        """
        # Store the selection in terms of the DF index
        selected_idx = self.map_df_index_to_idx(self.data_selected)
        if set(self.selected_idx) != set(selected_idx):
            self.selected_idx = selected_idx

    @on_trait_change("filtered_df", post_init=True)
    def update_plotter_datasource(self, new):
        """ Update plotter data if filtered data is changed so new plots made
        w/ new filtered data.
        """
        for plot_manager in self.plot_manager_list:
            plot_manager.data_source = new

    @on_trait_change("filtered_df, summary_index[]", post_init=True)
    def compute_summary(self):
        data = self.filtered_df
        if data is None or len(data) == 0:
            self.summary_df = DataFrame([])
            return self.summary_df

        try:
            summary = data.describe(exclude=self.categorical_dtypes)
        except ValueError as e:
            msg = "Failed to describe. Most likely due to no floating point " \
                  "columns found in data. Error was {}".format(e)
            logger.debug(msg)
            self.summary_df = DataFrame([])
            return self.summary_df

        all_summaries = [summary]
        for entry in self.summary_index:
            if entry.endswith("%") and entry not in summary.index:
                percent = float(entry[:-1])
                values = compute_percentile(data[summary.columns], percent)
                values_df = DataFrame({entry: values}).transpose()
                all_summaries.append(values_df)

        try:
            summary = concat(all_summaries, sort=True)
        except TypeError:
            # For pandas <= 0.20
            import warnings
            msg = "Pandas version 0.20 and before will not be supported long" \
                  " term: it is recommended to update."
            warnings.warn(msg)
            summary = concat(all_summaries)

        self.summary_df = summary.reindex(list(self.summary_index))
        return self.summary_df

    @on_trait_change("filtered_df", post_init=True)
    def compute_categorical_summary(self):
        data = self.filtered_df
        if data is None:
            self.summary_categorical_df = DataFrame([])
            return self.summary_categorical_df

        try:
            summary = data.describe(include=self.categorical_dtypes)
        except ValueError:
            # No categorical data
            self.summary_categorical_df = DataFrame([])
            return self.summary_categorical_df

        next_values = []
        next_freqs = []
        for col in summary.columns:
            value_counts = data[col].value_counts()
            if len(value_counts) <= 1:
                next_values.append(np.nan)
                next_freqs.append(np.nan)
            else:
                next_values.append(value_counts.index[1])
                next_freqs.append(int(value_counts.iloc[1]))

        adtl_data = {"next": next_values, "next_freq": next_freqs}
        adtl_summary = DataFrame(adtl_data, index=summary.columns).transpose()
        self.summary_categorical_df = concat([summary, adtl_summary]).reindex(
            DEFAULT_CATEG_SUMMARY_ELEMENTS)
        return self.summary_categorical_df

    def _filter_transformation_changed(self):
        self.recompute_filtered_df()

    def _filter_exp_changed(self, old, new):
        """ Recompute the filtered data from the filtering expression.
        """
        if not self.filter_auto_apply:
            return

        # Clean up new filter, removing space-like characters:
        new = self._clean_filter_exp(new)

        filter_equivalent = self._clean_filter_exp(old).replace(" ", "") == \
            new.replace(" ", "")
        if filter_equivalent:
            return

        try:
            self.recompute_filtered_df()
        except Exception as e:
            # query not fully formed syntactically?
            if self.filter_error_handling == "raise":
                raise
            elif self.filter_error_handling == "warn":
                msg = "Failed to filter DF with '{}'. Error was {}."
                logger.warn(msg.format(new, e))

    @on_trait_change("filtered_df, num_displayed_rows, show_selected_only, "
                     "selected_idx[]")
    def recompute_displayed_df(self):
        self.displayed_df = self._compute_displayed_df()

    def _source_df_changed(self):
        """ Update the filtered data and the sorting options and attribute.
        """
        self.recompute_filtered_df()

        index = self.source_df.index
        self.data_sorted = sorted(index) == index.tolist()
        if not self.data_sorted:
            self.sort_by_col = NO_SORTING_ENTRY
        else:
            self.sort_by_col = self.index_name

        self._update_column_descriptions()

    def _sort_by_col_changed(self, new):
        self.filtered_df = self._sort_df_by(self.filtered_df, new)
        # Remap the selections
        if self.data_selected:
            self.selected_idx = self.map_df_index_to_idx(self.data_selected)

    def _sort_df_by(self, df, by):
        """ Returns a sorted version the provided Dataframe by specified key.

        Parse the 'by' key to see if need to sort ascending or descending, or
        if needing to sort by the index or one of the columns.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to sort.

        by : str
            Name of the index or of the column to sort the DF by. Can contain a
            prefix to sort in descending order rather than the default
            ascending.
        """
        if by == NO_SORTING_ENTRY or df is None:
            return df

        if by.endswith(REVERSED_SUFFIX):
            by = by[:-len(REVERSED_SUFFIX)]
            ascending = False
        else:
            ascending = True

        if by == self.index_name:
            df = df.sort_index(ascending=ascending)
        else:
            df = df.sort_values(by=by, ascending=ascending)
        return df

    # Private interface -------------------------------------------------------

    def _update_column_descriptions(self):
        """ Remove column descriptions if a column has been removed.
        """
        descriptions = list(self.column_descr.keys())
        columns_present = set(self.source_df.columns)
        for col_name in descriptions:
            if col_name not in columns_present:
                self.column_descr.pop(col_name)

    @staticmethod
    def _clean_filter_exp(expr):
        """ Return cleaned up version of the expression provided.

        Replace all space like characters from the expression and double spaces
        by single spaces.

        Parameters
        ----------
        expr : str
            Expression to clean up.
        """
        for char in ["\r\n", "\n", "\t"]:
            expr = expr.replace(char, " ")

        while "  " in expr:
            expr = expr.replace("  ", " ")

        return expr

    def _compute_filtered_df(self):
        """ Compute filtered DF from source DF, filter expression & sort param.
        """
        if self.source_df is None:
            return None

        # Reset selection
        self.selected_idx = []

        if not self.filter_exp.strip():
            new_df = self.source_df
        else:
            query = self.filter_transformation(
                self._clean_filter_exp(self.filter_exp)
            )
            if not self._validate_query(query):
                msg = "Invalid filter expression error: {}.".format(query)
                logger.error(msg)
                raise InvalidQuery(msg)

            new_df = self.source_df.query(query)

        if self.sort_by_col:
            new_df = self._sort_df_by(new_df, self.sort_by_col)

        return new_df

    def _validate_query(self, query):
        """ Make sure query is usable and not just user still typing.

        Criteria is that there must be an operator for the query to have a
        chance of being evaluable. Designed to avoid results of queries like
        df.query(df.columns[0]) since these don't raise an error but mean
        something we won't be interested in (namely:
        df.loc[df[df.columns[0]], :]).
        """
        # In this list, '=' used to identify '==' or '>=' or '<=' more quickly:
        operators = ["=", ">", "<", "~", "not "]
        for op in operators:
            if op in query:
                return True

        # Not yet a query: skip evaluation: this is to avoid setting
        # filtered_df to an unusable value
        msg = "Skipping evaluation of query {} because no operator found."
        logger.debug(msg.format(query, operators))
        return False

    def _compute_displayed_df(self):
        """ Compute the displayed data, which is a subset of the filtered df.

        Rules:
        - Displayed DF is the filtered DF by default.
        - If show_selected_only is True, only show what is selected. Otherwise,
        - If it is too long and max_displayed is set.
        """
        filt_df = self.filtered_df
        if filt_df is None:
            return

        if self.show_selected_only:
            displayed_df = filt_df.iloc[self.selected_idx, :]
        elif 0 < self.num_displayed_rows < len(filt_df):
            displayed_df = filt_df.iloc[:self.num_displayed_rows, :]
        else:
            displayed_df = filt_df

        return displayed_df

    # Property getters/setters ------------------------------------------------

    @cached_property
    def _get_sort_by_col_list(self):
        if self.source_df is None:
            return []

        # The call to copy_and_sanitize in __init__ makes the data sorted by
        # the index:
        cols = [NO_SORTING_ENTRY, self.index_name,
                self.index_name + REVERSED_SUFFIX]

        for col in self.source_df.columns:
            cols.append(col)
            cols.append(col + REVERSED_SUFFIX)
        return cols

    @cached_property
    def _get_index_name(self):
        if self.source_df is None:
            return ""

        index_col = self.source_df.index.name
        if index_col is None:
            index_col = "index"
        return index_col

    # Traits initialization methods -------------------------------------------

    def _displayed_df_default(self):
        return self._compute_displayed_df()

    def _filtered_df_default(self):
        return self._compute_filtered_df()

    def _filter_transformation_default(self):
        return lambda x: x

    def _num_display_increment_default(self):
        return self.num_displayed_rows


def copy_and_sanitize(source_df, convert_dtypes=False, sort_index=True):
    """ Prepare the source DataFrame to create a DataFrameAnalyzer.

    This implements 3 or 4 transformation steps:
      - Make a copy of the original
      - Sanitize its column names so that they are valid variable names.
      - Sort the DF by its index so the sorting tool is consistent.
      - Optionally: convert all columns to float, and skip columns where that's
        not possible.
    """
    df = source_df.copy()

    # Convert column names to be valid variable names (so they can be used in
    # filter expressions)
    new_cols = []
    for col in source_df.columns:
        new_col = sanitize_string(col)
        # Make sure the cleaning operation doesn't lead to a column collision:
        new_col = add_suffix_if_exists(new_col, new_cols, suffix_patt="_{}")
        new_cols.append(new_col)

    df.columns = new_cols

    if convert_dtypes:
        # Try to convert columns to floats
        for col in df.columns:
            try:
                df[col] = df[col].astype("float64")
            except ValueError as e:
                msg = "Unable to convert column {} to floats (error was {})."
                msg = msg.format(col, e)
                logger.debug(msg)

    if sort_index:
        df = df.sort_index(ascending=True)

    return df


def compute_percentile(data, percent):
    """ Compute percentile for all float columns of a DF and return as Series.
    """
    float_mask = data.dtypes.apply(lambda x: np.issubdtype(x, np.number))
    float_cols = data.dtypes[float_mask].index
    f = partial(np.percentile, q=percent)
    return data[float_cols].apply(f, axis=0)
