
from traits.api import HasTraits, List


class Exportable(HasTraits):
    """ Object that can be converted to a dictionary.
    """
    #: List of attribute names to export to dictionary
    dict_keys = List

    def to_plot_kwargs(self):
        serialized = {}
        for key in self.dict_keys:
            attr = getattr(self, key)
            if isinstance(attr, Exportable):
                serialized[key] = attr.to_dict()
            else:
                serialized[key] = attr

        return serialized
