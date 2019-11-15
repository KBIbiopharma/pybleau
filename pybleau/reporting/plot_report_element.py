import logging
from os.path import splitext
import pandas as pd
import json
from six import string_types

from traits.api import Dict, Instance, Str

from .base_report_element import BaseReportElement

logger = logging.getLogger(__name__)


class PlotReportElement(BaseReportElement):
    """
    """
    #: Type of element to create
    element_type = Str("plot")

    #: Plot description, following the Vega-Lite specifications
    plot_desc = Dict

    #: Data to be plotted, loaded into a DataFrame
    source_data = Instance(pd.DataFrame)

    def __init__(self, **traits):
        if isinstance(traits.get("plot_desc", {}), string_types):
            traits["plot_desc"] = json.load(traits["plot_desc"])

        super(PlotReportElement, self).__init__(**traits)

        if self.source_data is None:
            data_info = self.plot_desc.pop("data", {})
            if "url" in data_info:
                data_url = data_info["url"]
                if splitext(data_url)[1] == ".h5":
                    self.source_data = pd.read_hdf(data_url)
                if splitext(data_url)[1] == ".csv":
                    self.source_data = pd.read_csv(data_url)
            elif "values" in data_info:
                self.source_data = pd.DataFrame(data_info["values"]).set_index(
                    "index")

    def to_report(self, backend):
        if self.source_data is None:
            msg = "No source data found."
            logger.exception(msg)
            raise ValueError(msg)

        elif self.plot_desc is None:
            msg = "No description found."
            logger.exception(msg)
            raise ValueError(msg)

        return super(PlotReportElement, self).to_report(backend=backend)

    def to_dash(self):
        """ Convert Vega plot desc to Plotly plot to be embedded into Dash.
        """
        import dash_core_components as dcc
        import dash_html_components as html
        import plotly.graph_objs as go
        from ..plotly_api.api import plotly_hist, plotly_scatter
        from ..vega_translators.vega_plotly import vega2plotly_hist, \
            vega2plotly_scatter

        try:
            desc = self.plot_desc
            if desc["mark"] == "point":
                kwargs = vega2plotly_scatter(desc, data=self.source_data)
                fig = plotly_scatter(target="fig", **kwargs)
            elif desc["mark"] == "bar" and desc["encoding"]["x"].get("bin", 0):
                kwargs = vega2plotly_hist(desc, data=self.source_data)
                fig = plotly_hist(target="fig", **kwargs)
            else:
                msg = "Plot element_type ({}) not supported with dash backend."
                msg = msg.format(self.plot_desc["mark"])
                logger.exception(msg)
                raise ValueError(msg)

        except Exception as e:
            msg = "Failed to build the plot. Error was {}.".format(e)
            logger.error(msg)
            fig = go.Figure()

        dash_graph = dcc.Graph(figure=fig)

        elements = [dash_graph]
        if self.plot_desc.get("description", ""):
            elements.append(
                html.P(children=self.plot_desc["description"])
            )

        return elements


if __name__ == "__main__":
    # These plot descriptions use the Vega-Lite standard. To learn more, see
    # https://vega.github.io/vega-lite/docs/
    # https://vega.github.io/vega-lite/tutorials/getting_started.html
    #
    # For a gallery of examples, https://vega.github.io/vega-lite/examples/.

    from app_common.std_lib.logging_utils import initialize_logging
    initialize_logging()

    desc = {
        "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
        "description": "A scatterplot showing horsepower and miles/gallons.",
        "config": {
            "view": {
                "height": 300,
                "width": 400
            }
        },
        "data": {"url": "step_analysis_df.h5"},
        "mark": "point",
        "encoding": {
            "x": {"field": "all_si_oil", "type": "quantitative"},
            "y": {"field": "all_prot_transluc", "type": "quantitative"},
            "color": {"field": "experiment", "type": "nominal"},
            "shape": {"field": "Lot", "type": "nominal"},

        }
    }

    desc2 = {
        "$schema": "https://vega.github.io/schema/vega-lite/v2.json",
        "description": "A simple bar chart with embedded data.",
        "data": {
            "values": [
                {"a": "A", "b": 28}, {"a": "B", "b": 55}, {"a": "C", "b": 43},
                {"a": "D", "b": 91}, {"a": "E", "b": 81}, {"a": "F", "b": 53},
                {"a": "G", "b": 19}, {"a": "H", "b": 87}, {"a": "I", "b": 52}
            ]
        },
        "mark": "bar",
        "encoding": {
            "x": {"field": "a", "type": "ordinal"},
            "y": {"field": "b", "type": "quantitative"}
        }
    }

    el = PlotReportElement(plot_desc=desc)
    dash_elements = el.to_dash()
