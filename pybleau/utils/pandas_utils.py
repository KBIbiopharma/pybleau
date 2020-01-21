import logging
from six import string_types
import pandas as pd
from os.path import isfile, splitext

logger = logging.getLogger(__name__)


def is_string_series(series, data=None):
    """ Returns whether a column contains strings.
    """
    if isinstance(series, string_types):
        series = get_col(data, series)

    if series.dtype == object:
        return all(isinstance(x, string_types) for x in series)

    return False


def get_col(df, col_name):
    """ Collect any column including the index.
    """
    if col_name in {df.index.name, "index"}:
        return df.index
    else:
        return df[col_name]


def pd_read_any(target, pandas_func=None, **kwargs):
    """ Wraps pd.read_csv, pd.read_excel, ... Load DF from any supported format

    Parameters
    ----------
    target : str
        Path to the file to load.

    kwargs : dict
        Keywords passed to the pandas read_** function. Refer to pandas
        documentation.
    """
    if not isfile(target):
        msg = "File not found: {}".format(target)
        logger.exception(msg)
        raise IOError(msg)

    if pandas_func is None:
        ext = splitext(target)[1].lower()
        if ext in [".xls", ".xlsx"]:
            pandas_func = pd.read_excel
        elif ext == ".csv":
            pandas_func = pd.read_csv
        elif ext in [".h5", ".hdf"]:
            pandas_func = pd.read_hdf
        else:
            msg = "Extension {} not supported by pd_read_any.".format(ext)
            logger.error(msg)
            return

    target = pandas_func(target, **kwargs)
    return target
