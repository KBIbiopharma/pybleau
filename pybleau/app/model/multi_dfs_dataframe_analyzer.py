import logging
import pandas as pd

from traits.api import Dict, Instance, Property

from .dataframe_analyzer import DataFrameAnalyzer

logger = logging.getLogger(__name__)


class MultiDataFrameAnalyzer(DataFrameAnalyzer):
    """ DataFrameAnalyzer where the source_df is a proxy for a list of DFs.
    """

    # Data storage attributes -------------------------------------------------

    source_df = Property(Instance(pd.DataFrame), depends_on="_source_dfs[]")

    _source_dfs = Dict

    _source_df_columns = Dict

    def __init__(self, **traits):

        if "source_df" in traits:
            traits["_source_dfs"] = {0: traits.pop("source_df")}
            traits["_source_df_columns"] = {0: traits.pop("source_df")}

        elif "_source_dfs" in traits and "_source_df_columns" not in traits:
            traits["_source_df_columns"] = {
                key: df.columns.tolist()
                for key, df in traits["_source_dfs"].items()
            }
        elif "_source_dfs" in traits and "_source_df_columns" in traits:
            assert traits["_source_dfs"].keys() == \
                traits["_source_df_columns"].keys()

        super(MultiDataFrameAnalyzer, self).__init__(**traits)

    def _get_source_df(self):
        return pd.concat(self._source_dfs.values())

    def _set_source_df(self, df):
        for key in self._source_dfs:
            self._source_dfs[key] = df[self._source_df_columns[key]]
