import logging
from os.path import dirname, join
from pandas import DataFrame
import json
import pandas as pd

from pybleau.reporting.plot_report_element import PlotReportElement
from pybleau.reporting.section_report_element import SectionReportElement
from pybleau.reporting.string_definitions import IDX_NAME_KEY, CONTENT_KEY, \
    DATASETS_KEY, DATA_KEY, DATA_FILE_KEY, DATA_FILE_KEY_KEY

logger = logging.getLogger(__name__)


def analysis_file2dash_reporter(analysis_filepath, include_explorers=True,
                                **report_kw):
    """ Build a Dash web app from a data exploration analysis description file.
    """
    from pybleau.reporting.api import DashReporter

    reporter = DashReporter(**report_kw)
    report_elements = []
    content = json.load(open(analysis_filepath))

    # Rebuild the datasets:
    datasets_data = content[DATASETS_KEY]
    datasets = {}
    for name, dataset_data in datasets_data.items():
        if DATA_KEY in dataset_data:
            idx_name = dataset_data[IDX_NAME_KEY]
            df = DataFrame(dataset_data[DATA_KEY]).set_index(idx_name)
        elif DATA_FILE_KEY in dataset_data:
            # DATA_FILE_KEY is a relative path compared to the analysis
            # description file:
            analysis_dir = dirname(analysis_filepath)
            data_path = join(analysis_dir, dataset_data[DATA_FILE_KEY])
            key = dataset_data[DATA_FILE_KEY_KEY]
            df = pd.read_hdf(data_path, key=key)
        else:
            msg = "Didn't find the data key nor the data file key. This file" \
                  " format isn't supported."
            logger.exception(msg)
            raise NotImplementedError(msg)

        datasets[name] = df

    desc_list = content[CONTENT_KEY]
    for i, desc in enumerate(desc_list):
        data = desc.pop("data")
        msg = "Adding plot {} with description {}".format(i, desc)
        logger.debug(msg)
        element = PlotReportElement(plot_desc=desc,
                                    source_data=datasets[data["name"]])
        report_elements.append(element)

    if include_explorers:
        report_elements.append(
            SectionReportElement("Data Explorers", section_level=2)
        )

    reporter.report_elements.extend(report_elements)
    reporter.generate_report()

    if include_explorers:
        for name, df in datasets.items():
            build_df_explorer(reporter.dash_app, df, df_id=name)

    return reporter


def build_df_explorer(app, df, df_id, title="", plot_style=None):
    """ Add to a dash app's children a set of dropdowns and a listening plot.

    Parameters
    ----------
    app : Dash application
        Application to add visual elements to.

    df : pd.DataFrame
        DataFrame to build the explorer for.

    df_id : str
        Unique string id to prepend to dash element ids, so listeners can be
        defined.

    title : str, optional
        Title to include as an h2 subsection if specified.

    plot_style : dict, optional
        Styling properties for the scatter plots created, for example to
        specify the marker size, alpha, ...,
    """
    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    import plotly.graph_objs as go

    from pybleau.plotly_api.api import plotly_scatter

    if plot_style is None:
        plot_style = {}

    columns = [""] + list(df.columns)
    drop_down_options = [{"label": name, "value": name} for name in columns]
    new_children = []
    if title:
        new_children.extend(
            [html.Br(),
             html.H2(children=title)]
        )

    new_children.extend(
        [
            html.Div(
                [
                    html.P(children='Select X dimension column:',
                           style={'display': 'inline-block'}),
                    dcc.Dropdown(
                        id=df_id + '-data-x-dropdown',
                        options=drop_down_options,
                        # initially display the first entry in the list
                        value="",
                        placeholder="Select a column to display along x",
                    ),
                    html.P(children='Select Y dimension column:',
                           style={'display': 'inline-block'}),
                    dcc.Dropdown(
                        id=df_id + '-data-y-dropdown',
                        options=drop_down_options,
                        # initially display the first entry in the list
                        value="",
                        placeholder="Select a column to display along y",
                    )
                ],
                style={'width': '48%', 'display': 'inline-block'}
            ),
            html.Div(
                [
                    html.P(children='Select column(s) to display on hover:',
                           style={'display': 'inline-block'}),
                    dcc.Dropdown(
                        id=df_id + '-data-hover-dropdown',
                        options=drop_down_options,
                        # initially display the first entry in the list
                        value=[],
                        placeholder="Select column(s) to display on hover",
                        multi=True
                    ),
                    html.P(children='Select color dimension column:',
                           style={'display': 'inline-block'}),
                    dcc.Dropdown(
                        id=df_id + '-data-color-dropdown',
                        options=drop_down_options,
                        # initially display the first entry in the list
                        value=None,
                        placeholder="Select column to display along the color "
                                    "dimension",
                    ),
                ],
                style={'width': '48%', 'float': 'right',
                       'display': 'inline-block'}
            ),
            html.Div([
                dcc.Graph(id=df_id+'-explorer',
                          # Will be initialized from the callback
                          figure=go.Figure())
            ],
                style={'width': '78%', 'display': 'inline-block'}
            )
        ]
    )

    app.layout.children.extend(new_children)

    # Then connect the drop down to the plot generation
    @app.callback(dash.dependencies.Output(df_id+'-explorer', 'figure'),
                  [dash.dependencies.Input(df_id+'-data-x-dropdown', 'value'),
                   dash.dependencies.Input(df_id+'-data-y-dropdown', 'value'),
                   dash.dependencies.Input(df_id+'-data-color-dropdown',
                                           'value'),
                   dash.dependencies.Input(df_id+'-data-hover-dropdown',
                                           'value')])
    def update_part_scatter(x_col_name, y_col_name, color_name, hover_props):
        """ Upon scatter plot properties, update the plotly figure.
        """
        if not x_col_name or not y_col_name:
            return go.Figure()

        return plotly_scatter(x_col_name, y_col_name, hover=hover_props,
                              data=df, hue=color_name,
                              marker_size=plot_style.get("marker_size", 12),
                              marker_alpha=plot_style.get("marker_alpha", 0.3),
                              target="fig")
