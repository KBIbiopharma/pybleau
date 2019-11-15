""" Base class to generate a report document. Target backends could include
Dash webapps, jupyter notebooks, static webpages, word documents, PDF
documents, rest/md documents, .... Backends will be developed as needed.
"""
import logging

from traits.api import File, HasStrictTraits, List, Str

from .base_report_element import BaseReportElement

logger = logging.getLogger(__name__)


class BaseReporter(HasStrictTraits):
    """ Base reporter object to generate a report targeting a specific backend.
    """
    #: Backend for the reporter
    backend = Str

    #: Location of the report
    report_url = Str

    #: Elements to insert in the report to build it
    report_elements = List(BaseReportElement)

    #: Title of the report
    report_title = Str("New Data Report")

    #: Path to the logo file to display at the top of the report
    report_logo = File

    def build_report_elements(self, element_descriptions):
        raise NotImplementedError()

    def generate_report(self):
        raise NotImplementedError()

    def open_report(self):
        raise NotImplementedError()
