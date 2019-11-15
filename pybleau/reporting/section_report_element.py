import logging

from traits.api import Enum, Str

from .base_report_element import BaseReportElement

logger = logging.getLogger(__name__)


class SectionReportElement(BaseReportElement):
    """
    """
    element_type = Str("section")

    section_level = Enum(list(range(1, 7)))

    align = Enum(["left", "center", "right"])

    def __init__(self, element_title="", **traits):
        if element_title:
            traits["element_title"] = element_title

        super(SectionReportElement, self).__init__(**traits)

    def to_dash(self):
        """ Convert Vega plot desc to Plotly plot to be embedded into Dash.
        """
        import dash_html_components as html

        klass_map = {1: html.H1, 2: html.H2, 3: html.H3, 4: html.H4,
                     5: html.H5, 6: html.H6}

        elements = [
            klass_map[self.section_level](children=self.element_title,
                                          style={'textAlign': self.align})
        ]
        return elements
