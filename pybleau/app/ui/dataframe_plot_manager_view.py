""" View for a DataFramePlotManager.
"""
import logging
import os

from enable.component_editor import ComponentEditor
from pyface.api import warning
from traits.api import Any, Bool, Button, Enum, Instance, \
    Int, List
from traitsui.api import EnumEditor, HGroup, Item, Label, ModelView, \
    Spring, TableEditor, VGroup, View, VSplit, ObjectColumn
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.menu import CancelButton, OKButton

from pybleau.app.model.dataframe_plot_manager import CONTAINER_IDX_REMOVAL, \
    DataFramePlotManager
from pybleau.app.model.multi_canvas_manager import CONTAINER_TRAIT_NAME
from pybleau.app.model.tests.test_plot_template_manager import \
    FakePlotTemplateInteractor
from pybleau.app.plotting.i_plot_template_interactor import \
    IPlotTemplateInteractor
from pybleau.app.ui.base_templates_list_dlg import BaseTemplateListDlg, \
    ManageTemplatesHandler

logger = logging.getLogger(__name__)

DEFAULT_CONTAINER_SIZE = 400

DEFAULT_PLOT_CONTROL_SIZE = 170

AUTO_TARGET_CONTAINER = "auto"


class DataFramePlotManagerView(ModelView):
    """ View for a DataFramePlotManager.

    This UI allows to manipulate the manager, add new plots to it, export them,
    and expose its contained_plots list for user interaction.

    TODO: Allow to change the layout of the container after creation.
    """
    #: Plot manager being visualized
    model = Instance(DataFramePlotManager)

    #: View class to use. Modify to customize.
    view_klass = Any(View)

    #: Control to show/hide the plot list table
    show_plot_list = Bool(True)

    #: Launcher to add new plots
    new_plot_button = Button("Add Plot...")

    #: Button to export plot list
    export_plots_button = Button("Export plots")

    #: List of column names to display in the plot controls
    plot_control_cols = List

    def traits_view(self):
        self.raise_dlg_if_failed_plots()
        plot_list_editor = self.build_plot_list_editor()

        tooltip = "Strategy for auto-selecting the target row: 0 -> first " \
                  "row, 1 -> last row, 2 -> new row."
        view = self.view_klass(
            VGroup(
                VSplit(
                    VGroup(
                        Item("model.contained_plots", editor=plot_list_editor,
                             label="Plot list",
                             height=DEFAULT_PLOT_CONTROL_SIZE),
                        show_border=True, visible_when="show_plot_list"
                    ),
                    VGroup(
                        HGroup(
                            Item("show_plot_list",
                                 label=u"\u2191 Show plot list"),
                            Spring(),
                            Item("model.canvas_manager.multi_container_mode",
                                 label="Mode", tooltip=tooltip),
                        ),
                        self._build_container_group(),
                        VGroup(
                            Spring(),
                            HGroup(
                                Spring(),
                                Label("Create new plots with button below"),
                                Spring(),
                            ),
                            Spring(),
                            visible_when="len(model.contained_plots) == 0"
                        ),
                    ),
                ),
                HGroup(
                    Item('new_plot_button', show_label=False),
                    Spring(),
                    Item('export_plots_button', show_label=False,
                         enabled_when="len(model.contained_plots) > 0"),
                ),
            ),
            resizable=True, width=800, scrollable=True, height=1000
        )
        return view

    def build_plot_list_editor(self):
        """ Build a table editor for the model's list of PlotDescriptors.
        """
        num_containers = self.model.canvas_manager.num_container_managers
        container_idx_vals = list(range(num_containers)) + [
            CONTAINER_IDX_REMOVAL]

        name_to_col = {
            "id": ObjectColumn(name='id', style="readonly",
                               cell_color="lightgrey"),
            "plot_title": ObjectColumn(name="plot_title"),
            # The format_func is called with an argument, the object to
            # display, therefore the x argument placeholder:
            'edit_plot_style': ObjectColumn(name='edit_plot_style',
                                            label="Edit Style",
                                            format_func=lambda x: "Edit"),
            "visible": CheckboxColumn(name='visible'),
            "frozen": CheckboxColumn(
                name='frozen', tooltip="Freeze the plot and skip updates when "
                                       "source data changes"),
            "plot_type": ObjectColumn(name='plot_type', style="readonly",
                                      cell_color="lightgrey"),
            "x_col_name": ObjectColumn(name='x_col_name', style="readonly",
                                       cell_color="lightgrey",
                                       label="X column"),
            'x_axis_title': ObjectColumn(name='x_axis_title'),
            "y_col_name": ObjectColumn(name='y_col_name', style="readonly",
                                       cell_color="lightgrey",
                                       label="Y column"),
            'y_axis_title': ObjectColumn(name='y_axis_title'),
            'secondary_y_axis_title': ObjectColumn(
                name='secondary_y_axis_title', label="Second. Y title"
            ),
            "z_col_name": ObjectColumn(name='z_col_name', style="readonly",
                                       cell_color="lightgrey",
                                       label="Z column (color)"),
            'z_axis_title': ObjectColumn(name='z_axis_title'),
            "data_filter": ObjectColumn(name='data_filter',
                                        label="Analyzer data filter",
                                        style="readonly"),
            'container_idx': ObjectColumn(
                name='container_idx',
                editor=EnumEditor(values=container_idx_vals),
                label="Move/Delete"
            )
        }

        columns = [name_to_col[col] for col in self.plot_control_cols]

        plot_list_editor = TableEditor(
            columns=columns,
            auto_size=True,
            sortable=True,
            h_size_policy="expanding",
            editable=True,
            edit_on_first_click=False,
            reorderable=False,
            row_factory=None,
            deletable=False
        )
        return plot_list_editor

    def _build_container_group(self):
        """ Build the view group containing all plot containers.
        """
        is_horiz = self.model.canvas_manager.container_layout_type == "horizontal"  # noqa
        cont_height = DEFAULT_CONTAINER_SIZE if is_horiz else -1
        cont_width = -1 if is_horiz else DEFAULT_CONTAINER_SIZE
        group_klass = VGroup if is_horiz else HGroup

        # Build items for each of the containers available on the model:
        trait = "model.canvas_manager." + CONTAINER_TRAIT_NAME + ".container"
        item0 = Item(trait.format(0),
                     editor=ComponentEditor(),
                     show_label=False, height=cont_height, width=cont_width,
                     visible_when="len(model.contained_plots) > 0")

        container_items = [item0]
        for i in range(1, self.model.canvas_manager.num_container_managers):
            item = Item(trait.format(i), editor=ComponentEditor(),
                        show_label=False, height=cont_height, width=cont_width,
                        visible_when="{} in model.containers_in_use".format(i))

            container_items.append(item)

        return group_klass(*container_items)

    # Private interface -------------------------------------------------------

    def raise_dlg_if_failed_plots(self):
        """ If some plots couldn't be rebuilt in the model, issue a warning.
        """
        if self.model.failed_plots:
            error_msgs = []
            for desc in self.model.failed_plots:
                msg = "Failed to recreate plot number {} ({} of '{}' vs '{" \
                      "}', z_col '{}'). It will need to be recreated manually."
                msg = msg.format(desc.id, desc.plot_type, desc.x_col_name,
                                 desc.y_col_name, desc.z_col_name)
                error_msgs.append(msg)

            msg = "\n\n".join(error_msgs)
            warning(None, msg)

    # Traits listeners --------------------------------------------------------

    def _new_plot_button_fired(self):
        """ Create a new plot:

        1. Use a PlotTypeSelector to allow user to select the plot type.
        2. Create and display a PlotConfigurator for the required type.
        3. Create and add the new plot(s).
        """
        selector = PlotTypeSelector(
            view_klass=self.view_klass,
            num_containers=self.model.canvas_manager.num_container_managers,
            container_idx=AUTO_TARGET_CONTAINER,
            plot_types=self.model.plot_types,
            model=self.model.template_manager
        )
        ui = selector.edit_traits(kind="livemodal")
        if not ui.result:
            return

        plot_type = selector.plot_type

        if plot_type in self.model.custom_configs:
            initial_creation = False
            configurator = self.create_config_for_custom_type(plot_type)
        else:
            initial_creation = True
            next_plot_num = len(self.model.contained_plots) + 1
            if plot_type.startswith("Multi"):
                new_plot_default_title = "Plot {i}"
            else:
                new_plot_default_title = "Plot {}".format(next_plot_num)

            config_klass = self.model.plot_configs[plot_type]
            configurator = config_klass(data_source=self.model.data_source,
                                        plot_title=new_plot_default_title,
                                        view_klass=self.view_klass)
            ui = configurator.edit_traits(kind="livemodal")
            if not ui.result:
                return

        if selector.container_idx == AUTO_TARGET_CONTAINER:
            selector.container_idx = -1

        self.model.add_new_plot(plot_type, configurator,
                                container=selector.container_idx,
                                initial_creation=initial_creation)

    def create_config_for_custom_type(self, plot_type):
        if self.model.template_interactor is None:
            msg = f"A {type(self.model)} requires an " \
                  f"{type(IPlotTemplateInteractor)} to load templates."
            logger.exception(msg)
            raise AttributeError(msg)
        interactor = self.model.template_interactor
        filepath = os.path.join(interactor.get_template_dir(), plot_type +
                                interactor.get_template_ext())
        loader = interactor.get_template_loader()
        configurator = loader(filepath)
        configurator.data_source = self.model.data_source
        configurator.source_template = plot_type
        return configurator

    def _export_plots_button_fired(self):
        from pybleau.app.io.dataframe_plot_manager_exporter import \
            DataFramePlotManagerExporter

        exporter = DataFramePlotManagerExporter(df_plotter=self.model,
                                                view_klass=self.view_klass)
        exporter.export()

    # Traits initializers -----------------------------------------------------

    def _plot_control_cols_default(self):
        return ["id", "plot_title", 'edit_plot_style', "visible", "frozen",
                "plot_type", "x_col_name", 'x_axis_title', "y_col_name",
                'y_axis_title', "secondary_y_axis_title", "z_col_name",
                'z_axis_title', "data_filter", 'container_idx']


class PlotTypeSelector(BaseTemplateListDlg):
    """ Tiny UI to select the type of plot to create.
    """
    #: Selected plot type
    plot_type = Enum(values="plot_types")

    #: Selected container for the future plot
    container_idx = Any

    #: Type of container layout to describe whether a row or a column is
    #: selected when selecting a container:
    container_layout_type = Enum(["horizontal", "vertical"])

    #: Total number of containers available to place the future plot
    num_containers = Int(1)

    def traits_view(self):
        if self.container_layout_type == "horizontal":
            idx_description = "Row"
        else:
            idx_description = "Column"

        values = [AUTO_TARGET_CONTAINER] + list(range(self.num_containers))
        view = self.view_klass(
            HGroup(
                Item('plot_type', label="Select plot type"),
                Item('container_idx',
                     editor=EnumEditor(values=values),
                     label="{} #".format(idx_description),
                     visible_when="num_containers > 1",
                     tooltip="Can be changed later in the plot list."),
            ),
            buttons=[OKButton, CancelButton, self.man_temp_button],
            title="Select Plot Type and {}".format(idx_description),
            resizable=True,
            handler=ManageTemplatesHandler()
        )
        return view


if __name__ == "__main__":
    plot_manager = DataFramePlotManager(
        template_interactor=FakePlotTemplateInteractor()
    )
    selector = PlotTypeSelector(
        num_containers=plot_manager.canvas_manager.num_container_managers,
        container_idx=AUTO_TARGET_CONTAINER,
        plot_types=plot_manager.plot_types,
        model=plot_manager.template_manager
    )
    ui = selector.configure_traits()
