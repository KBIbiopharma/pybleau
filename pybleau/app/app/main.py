
import logging
from six import string_types

from pybleau.app.ui.dataframe_analyzer_model_view import DataFrameAnalyzer, \
    DataFrameAnalyzerView, DataFramePlotManager
from pybleau.utils.pandas_utils import pd_read_any

logger = logging.getLogger(__name__)


def main(target, read_func_kw=None, ui_kind="start", **kwargs):
    """" Launch the DF explorer as a standalone application.

    Parameters
    ----------
    target : str, pd.DataFrame
        Pandas dataframe, or file containing a table to be loaded.

    read_func_kw : dict, optional
        Dictionary of keywords to pass the pandas read function to load the
        target dataframe.

    ui_kind : str, optional
        Type of window to create. Passed to Traitsui's `edit_traits`. Use
        "start" to create the GUI event loop instead of using `edit_traits`.

    kwargs : dict
        Keywords to control the attributes of the instance of
        `pybleau.app.ui.dataframe_analyzer_model_view.DataFrameAnalyzerView`
        created.
    """
    if read_func_kw is None:
        read_func_kw = {}

    if isinstance(target, string_types):
        target = pd_read_any(target, **read_func_kw)

    analyzer = DataFrameAnalyzer(source_df=target)
    view = DataFrameAnalyzerView(model=analyzer, **kwargs)
    if ui_kind == "start":
        view.configure_traits()
    else:
        view.edit_traits(kind=ui_kind)
