

from traits.api import Any, Enum, Int, List
from traitsui.api import HGroup, Item, RangeEditor, View
from kiva.trait_defs.kiva_font_trait import font_families

from .exportable import Exportable

DEFAULT_AXIS_LABEL_FONT_SIZE = 18

DEFAULT_TITLE_FONT_SIZE = 18

DEFAULT_TITLE_FONT = "modern"


class TitleStyle(Exportable):

    #: Font used to draw the title
    font_name = Enum(DEFAULT_TITLE_FONT, values="_all_fonts")

    #: Font size used to draw the title
    font_size = Int(DEFAULT_AXIS_LABEL_FONT_SIZE)

    #: List of all available fonts
    _all_fonts = List

    #: View klass. Override to customize the views, for example their icon
    view_klass = Any(default_value=View)

    def traits_view(self):
        return self.view_klass(
            HGroup(
                Item("font_name"),
                Item('font_size',
                     editor=RangeEditor(low=9, high=32))
            )
        )

    # Traits initialization methods -------------------------------------------
    def _dict_keys_default(self):
        return ["font_name", "font_size"]

    def __all_fonts_default(self):
        return sorted(list(font_families.keys()))


if __name__ == "__main__":
    TitleStyle().configure_traits()
