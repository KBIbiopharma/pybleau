from traits.api import HasStrictTraits, Dict, Callable, Any, Str, List, Button
from traitsui.api import VGroup, Item, View


class ScrollableButtonListView(HasStrictTraits):
    """ Provides a view for a dict of str:str conversions to Buttons

    Give this class a `dict`, and it will turn those `key:value` pairs
    into a view full of `Buttons`. Clicking any `Button` calls the
    `handler` with the key as the `event.name`.
    The keys must be strings that are usable as trait names; the values can
    be any string.
    """

    #: Dict of trait-valid name strings as keys and any string as values
    traits_and_names = Dict

    #: Function to call when any of the resulting `Button` objects are clicked
    handler = Callable

    #: Class to use to create TraitsUI window to open controls
    view_klass = Any(default_value=View)

    #: Name for the VGroup
    group_label = Str

    #: Internal list of trait names
    _trait_names = List

    def __init__(self, traits_and_names, handler, group_label="", **traits):
        super(ScrollableButtonListView, self).__init__(**traits)
        self.traits_and_names = traits_and_names
        self.handler = handler
        self.group_label = group_label
        self._make_trait_names()

    def _make_trait_names(self):
        # add the trait names to this object, and connect the handler function
        for trait_name, label in self.traits_and_names.items():
            self._trait_names.append(trait_name)
            self.add_trait(trait_name, Button(str(label)))
            self.observe(self.handler, trait_name)

    def traits_view(self):
        items = [Item(n, show_label=False) for n in self._trait_names]

        return self.view_klass(
            VGroup(*items, label=self.group_label),
            scrollable=True
        )
