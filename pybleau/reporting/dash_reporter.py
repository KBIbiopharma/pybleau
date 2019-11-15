""" Class to drive the generation of a data report using Dash as the backend.
"""
import logging
from uuid import uuid4
from flask import Flask
import dash
import dash_html_components as html

from traits.api import Any, Bool, Int, List, Str

from .base_reporter import BaseReporter
from .section_report_element import SectionReportElement
from .image_report_element import ImageReportElement

logger = logging.getLogger(__name__)


class DashReporter(BaseReporter):
    """ Base reporter object to generate a report targeting a specific backend.
    """
    #: Flask WSGI application dash builds on
    flask_app = Any

    #: Dash top-level application object
    dash_app = Any

    #: Port to serve the fask application on
    port = Int(8053)

    #: List of CSS style sheets to style the web app
    stylesheets = List

    #: Whether to require authentication to access the webapp
    include_auth = Bool(False)

    # BaseReport attributes ---------------------------------------------------

    #: Backend for the reporter
    backend = Str("dash")

    #: Title of the report
    report_title = Str("New Dash Report")

    def generate_report(self):
        """ Initialize the report and insert all elements.
        """
        self.initialize_report()
        self.insert_report_elements()

    def initialize_report(self):
        """ Initialize the report by creating a Dash app, adding logo & title.
        """
        self.dash_app = dash.Dash(
            __name__, external_stylesheets=self.stylesheets,
            server=self.flask_app
        )

        children = []
        if self.report_logo:
            report_logo_element = ImageReportElement(self.report_logo,
                                                     align="right").to_dash()
            children.extend(report_logo_element)

        if self.report_title:
            title_element = SectionReportElement(self.report_title,
                                                 align='center').to_dash()
            children.extend(title_element)

        self.dash_app.layout = html.Div(children=children)

    def insert_report_elements(self):
        """ Insert all report elements specified.
        """
        for element in self.report_elements:
            app_elements = element.to_report(self.backend)
            self.dash_app.layout.children.extend(app_elements)

    def open_report(self):
        """ Start the Dash server, and print server info.
        """
        if self.include_auth:
            import dash_auth
            pw = str(uuid4())
            logger.warning("Password for this session: {}".format(pw))
            pass_pairs = [('jrocher', pw)]
            dash_auth.BasicAuth(self.dash_app, pass_pairs)

        self.dash_app.run_server(debug=True, port=self.port)

    # Traits initialization methods -------------------------------------------

    def _stylesheets_default(self):
        return ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    def _flask_app_default(self):
        return Flask(__name__)
