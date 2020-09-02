import logging
import pandas as pd

from traits.api import Dict, Instance, Property

from .dataframe_analyzer import copy_and_sanitize, DataFrameAnalyzer

logger = logging.getLogger(__name__)


class MultiDataFrameAnalyzer(DataFrameAnalyzer):
    """ DataFrameAnalyzer where the source_df is a proxy for a list of DFs.
    """

    # Data storage attributes -------------------------------------------------

    source_df = Property(Instance(pd.DataFrame), depends_on="_source_dfs[]")

    _source_dfs = Dict

    _source_df_columns = Dict

    def __init__(self, convert_source_dtypes=False, data_sorted=True,
                 **traits):

        if "source_df" in traits:
            df = traits.pop("source_df")
            traits["_source_dfs"] = {0: df}

        if "_source_dfs" in traits and isinstance(traits["_source_dfs"], list):
            dfs = traits["_source_dfs"]
            traits["_source_dfs"] = {i: df for i, df in enumerate(dfs)}

        if "_source_dfs" in traits:
            known_cols = set()
            for df in traits["_source_dfs"].values():
                new_cols = set(df.columns)
                column_overlap = known_cols & new_cols
                if column_overlap:
                    msg = "Dataframes provided have overlapping columns it " \
                          "will be ambiguous what data should be stored where."
                    logger.exception(msg)
                    raise ValueError(msg)

                known_cols = known_cols | new_cols

        if "_source_dfs" in traits and "_source_df_columns" not in traits:
            traits["_source_df_columns"] = {
                key: df.columns.tolist()
                for key, df in traits["_source_dfs"].items()
            }
        elif "_source_dfs" in traits and "_source_df_columns" in traits:
            df_map_keys = list(traits["_source_dfs"].keys())
            col_map_keys = list(traits["_source_df_columns"].keys())
            if df_map_keys != col_map_keys:
                msg = "Keys of _source_dfs and _source_df_columns aren't the" \
                      " same ({} vs {}).".format(df_map_keys, col_map_keys)
                logger.exception(msg)
                raise ValueError(msg)

        if "_source_dfs" in traits:
            for key, df in traits["_source_dfs"].items():
                traits["_source_dfs"][key] = copy_and_sanitize(
                    df, convert_dtypes=convert_source_dtypes,
                    sort_index=data_sorted
                )

        super(MultiDataFrameAnalyzer, self).__init__(
            convert_source_dtypes=convert_source_dtypes,
            data_sorted=data_sorted, **traits
        )

        # If the index isn't unique, selection functionalities will break.
        if isinstance(self.source_df, pd.DataFrame):
            index = self.source_df.index
            if len(index.unique()) != len(index):
                # The breakage will come from the fact that the translation
                # between a selection position to a selected index isn't
                # bijective:
                msg = "The index of the source DataFrame isn't unique. Some " \
                      "selection functionality will break. The DF must be " \
                      "modified"
                logger.exception(msg)
                raise NotImplementedError(msg)

    def _get_source_df(self):
        """ Rebuild the source_df proxy from _source_dfs.
        """
        if self._source_dfs:
            return pd.concat(self._source_dfs.values(), axis=1)

    def _set_source_df(self, df):
        """ Set the source_df proxy to a new value.

        If no source_dfs stored, set this 1 for key 0. If there are source_dfs,
        update them.
        """
        if not self._source_dfs:
            self._source_dfs[0] = df
        else:
            current_cols = []
            for cols in self._source_df_columns.values():
                current_cols += cols

            new_cols = set(df.keys()) - set(current_cols)
            if new_cols:
                msg = "There are new columns ({}) compared to the existing " \
                      "_source_dfs: cannot set the source_df as a whole. " \
                      "Please update the _source_dfs dict to resolve " \
                      "ambiguity.".format(new_cols)
                logger.exception(msg)
                raise NotImplementedError(msg)

            for key in self._source_dfs:
                self._source_dfs[key] = df[self._source_df_columns[key]]
