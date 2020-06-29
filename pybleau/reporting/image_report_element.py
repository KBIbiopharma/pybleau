import logging

from traits.api import Enum, File, Str

from .base_report_element import BaseReportElement

logger = logging.getLogger(__name__)


class ImageReportElement(BaseReportElement):
    """ Report element to embed an image.
    """
    #: Type of the element created
    element_type = Str("image")

    #: Path to the image file to embed
    filepath = File

    #: Where to place the image in the document's width
    align = Enum(["left", "center", "right"])

    def __init__(self, filepath="", **traits):
        if filepath:
            traits["filepath"] = filepath

        super(ImageReportElement, self).__init__(**traits)

    def to_dash(self):
        """ Convert Vega plot desc to Plotly plot to be embedded into Dash.
        """
        import dash_html_components as html
        import base64

        with open(self.filepath, 'rb') as f:
            img_content = f.read()

        encoded_image = base64.b64encode(img_content)
        img = html.Img(src='data:image/png;base64,{}'.format(
            encoded_image.decode())
        )
        img_element = html.Div(children=[img], style={'textAlign': self.align})
        return [img_element]
