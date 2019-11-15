
from traits.api import HasStrictTraits, Str


class BaseReportElement(HasStrictTraits):
    element_title = Str

    element_type = Str

    def to_report(self, backend):
        if backend == "dash":
            return self.to_dash()
        else:
            raise NotImplementedError()

    def to_dash(self, *args, **kwargs):
        raise NotImplementedError()


class SubSectionReportElement(BaseReportElement):
    """
    """


class TextReportElement(BaseReportElement):
    """
    """


class ImageReportElement(BaseReportElement):
    """
    """


class ImageListReportElement(BaseReportElement):
    """
    """


class TableReportElement(BaseReportElement):
    """
    """
