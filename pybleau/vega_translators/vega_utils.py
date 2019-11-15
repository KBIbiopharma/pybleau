
class UnsupportedVegaSchemaVersion(NotImplementedError):
    pass


def df_to_vega(df):
    """ Convert a Pandas dataframe to the format Vega-Lite expects.
    """
    return [row[1].to_dict() for row in df.reset_index().iterrows()]
