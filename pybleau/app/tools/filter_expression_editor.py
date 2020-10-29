from traits.has_traits import HasStrictTraits
from traits.api import Str, Any
from traitsui.api import VGroup, Item, OKCancelButtons, View


class FilterExpressionEditorView(HasStrictTraits):
    """ Provides a resizeable edit view of the filter string (or any string).
    """

    #: Expression representing the dataframe filter
    exp = Str

    #: Class to use to create TraitsUI window to open controls
    view_klass = Any(View)

    def traits_view(self):
        view = self.view_klass(
            VGroup(
                Item("exp", style="custom", show_label=False),
                show_border=True
            ),
            resizable=True,
            buttons=OKCancelButtons,
            title="Edit the filter...",
        )
        return view


if __name__ == "__main__":
    test = FilterExpressionEditorView(exp="test string")
    test.edit_traits(kind="livemodal")
