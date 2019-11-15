from six import string_types


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
