import json
from os.path import abspath, basename, dirname, expanduser, isdir, isfile, \
    join, splitext
import os
import logging
from tempfile import mkstemp
from zipfile import ZipFile
import pandas as pd
from six import string_types

from pyface.api import error, information
from traits.api import Any, Bool, cached_property, Directory, Enum, File, \
    HasStrictTraits, Instance, List, Property, Range, Str
from traitsui.api import FileEditor, HGroup, Item, Label, OKCancelButtons, \
    Spring, VGroup, View

from app_common.chaco.plot_io import save_plot_to_file
from app_common.std_lib.filepath_utils import open_file, string2filename
from app_common.std_lib.logging_utils import ACTION_LEVEL

from ...vega_translators.vega_chaco import chaco2vega
from ...vega_translators.vega_utils import df_to_vega
from ...reporting.string_definitions import CONTENT_KEY, DATA_FILE_KEY, \
    DATA_FILE_KEY_KEY, DATA_KEY, DATASETS_KEY, IDX_NAME_KEY
from .plot_io_utils import plot_data2dataframes

logger = logging.getLogger(__name__)

DEFAULT_DATASET_NAME = "Source data"

DATA_FILE_COMP_KEY = "compression_info"

EXTERNAL_DATA_FNAME = "exported_data"

DEFAULT_EXPORT_FILENAME = "exported_plots"

IMG_FORMAT = "Image Folder"

VEGA_FORMAT = "Vega Plot Descriptions (EXPERIMENTAL)"

PPT_FORMAT = "Powerpoint"

METHOD_MAP = {IMG_FORMAT: "to_folder", VEGA_FORMAT: "to_vega",
              PPT_FORMAT: "to_pptx"}

EXPORT_NO = "No"

EXPORT_YES = "Yes"

EXPORT_INLINE = "In-line"

EXPORT_IN_FILE = "In-file"

EXPORT_SEPARATE = "Separate file"


class DataFramePlotManagerExporter(HasStrictTraits):
    """ Exporter of a DataFramePlotManager content to various formats.
    """
    df_plotter = Instance("pybleau.app.api.DataFramePlotManager")

    export_format = Enum([IMG_FORMAT, PPT_FORMAT, VEGA_FORMAT])

    #: Whether to, and how to, export the data behind the plots
    export_data = Enum(values="_export_data_options")

    export_each_plot_data = Bool

    #: The ways to export the data depend on the target format
    _export_data_options = Property(List(Str), depends_on="export_format")

    data_filename = Str(EXTERNAL_DATA_FNAME)

    data_format = Enum([".csv", ".xlsx", ".h5"])

    #: Whether to skip plots whose visible flag is off
    skip_hidden = Bool(True)

    #: Target directory
    target_dir = Directory

    target_file = File

    view_klass = Any(View)

    interactive = Bool(True)

    # Image format specific parameters ----------------------------------------

    image_format = Enum(["PNG", "JPG", "BMP", "TIFF", "EPS"])

    image_dpi = Range(low=50, high=100, value=72)

    filename_from_title = Bool(True)

    # Image format specific parameters ----------------------------------------

    overwrite_file_if_exists = Bool(False)

    json_index = Range(low=0, high=4, value=2)

    _many_plots = Bool

    # PPT format specific parameters ------------------------------------------

    presentation_title = Str("New Presentation")

    presentation_subtitle = Str

    def traits_view(self):
        is_ppt = "export_format == '{}'".format(PPT_FORMAT)
        is_vega = "export_format == '{}'".format(VEGA_FORMAT)
        is_img = "export_format=='{}'".format(IMG_FORMAT)

        num_plots = len(self.df_plotter.contained_plots)
        inline_warning = "Warning: exporting data inline can use a lot of " \
                         "file storage because the same data is stored inside"\
                         " each of the {} plots.".format(num_plots)
        inline_visible_when = "_many_plots and export_data=='{}'".format(
            EXPORT_INLINE)
        dat_file_visible_when = "export_data in ['{}', '{}']".format(
            EXPORT_YES, EXPORT_SEPARATE
        )

        view = self.view_klass(
            VGroup(
                HGroup(
                    Spring(),
                    Item("export_format"),
                    Spring()
                ),
                VGroup(
                    Item('target_dir', visible_when=is_img),
                    HGroup(
                        Item('target_file',
                             editor=FileEditor(dialog_style='save')),
                        Item("overwrite_file_if_exists",
                             label="Overwrite report file if exists?"),
                        visible_when=is_ppt + " or " + is_vega
                    ),
                    Item("overwrite_file_if_exists",
                         label="Overwrite image files if exist?",
                         visible_when=is_img),
                    Item('skip_hidden', label="Skip hidden plots"),
                    label="General Parameters", show_border=True
                ),
                VGroup(
                    HGroup(
                        Item('export_data', label="Export data?"),
                        Item("export_each_plot_data",
                             label="Export each plot's data?",
                             visible_when="export_data=='{}'".format(EXPORT_YES))  # noqa
                    ),
                    HGroup(
                        Item("data_filename"),
                        Item("data_format"),
                        visible_when=dat_file_visible_when
                    ),
                    HGroup(
                        Label(inline_warning),
                        visible_when=inline_visible_when
                    ),
                    label="Data Parameters", show_border=True
                ),
                VGroup(
                    HGroup(
                        Item('image_format'),
                        Item('image_dpi'),
                    ),
                    Item("filename_from_title"),
                    visible_when=is_img, label="Image Parameters",
                    show_border=True
                ),
                VGroup(
                    Item("presentation_title"),
                    Item("presentation_subtitle"),
                    label="Powerpoint Parameters", show_border=True,
                    visible_when=is_ppt
                ),
            ),
            buttons=OKCancelButtons,
            title="Export plots",
            resizable=True, width=600
        )
        return view

    # Public interface --------------------------------------------------------

    def export(self):
        """ Launch view to select parameters and export content to file.
        """
        if self.interactive:
            ui = self.edit_traits(kind="livemodal")

        if not self.interactive or ui.result:
            msg = f"Exporting plot content to {self.export_format}."
            logger.log(ACTION_LEVEL, msg)

            to_meth = getattr(self, METHOD_MAP[self.export_format])
            try:
                to_meth()
                if self.interactive:
                    target = self.target_dir if self.export_format != \
                                              PPT_FORMAT else self.target_file
                    open_file(target)

            except Exception as e:
                msg = f"Failed to export the plot list. Error was {e}."
                logger.exception(msg)
                if self.interactive:
                    error(None, msg)

    def to_folder(self, **kwargs):
        """ Export all plots as separate images files PNG, JPEG, ....
        """
        if not isdir(self.target_dir):
            os.makedirs(self.target_dir)

        plot_list = self.df_plotter.contained_plots

        if self.export_data == EXPORT_YES:
            if not self.export_each_plot_data:
                self._export_data_source_to_file(target=self.target_dir)
            else:
                fname = self.data_filename+self.data_format
                data_path = join(self.target_dir, fname)
                self._export_plot_data_to_file(plot_list, data_path=data_path)

        if self.filename_from_title:
            filename_patt = "{i}_{title}.{ext}"
        else:
            filename_patt = "plot_{i}.{ext}"

        for i, desc in enumerate(plot_list):
            if self.skip_hidden and not desc.visible:
                continue

            if self.filename_from_title:
                title = string2filename(desc.plot_title)
            else:
                title = ""

            filename = filename_patt.format(i=i, ext=self.image_format,
                                            title=title)
            filepath = join(self.target_dir, filename)
            if isfile(filepath) and not self.overwrite_file_if_exists:
                msg = "Target image file path specified already exists" \
                      ": {}. Move the file or select the 'overwrite' checkbox."
                msg = msg.format(filepath)
                logger.exception(msg)
                raise IOError(msg)

            save_plot_to_file(desc.plot, filepath=filepath, dpi=self.image_dpi,
                              **kwargs)

    def to_pptx(self, **kwargs):
        """ Export all plots as a PPTX presentation with a plot per slide.
        """
        # Protect imports so pptx remains an optional import
        from pybleau.reporting.pptx_utils import image_to_slide, Presentation,\
            title_slide

        target_dir = dirname(self.target_file)
        data_fname = self.data_filename+self.data_format
        target_data_file = join(target_dir, data_fname)
        if not isdir(target_dir):
            os.makedirs(target_dir)

        plot_list = self.df_plotter.contained_plots

        if self.export_data == EXPORT_YES:
            if not self.export_each_plot_data:
                self._export_data_source_to_file(target=target_data_file)
            else:
                self._export_plot_data_to_file(plot_list,
                                               data_path=target_data_file)

        if splitext(self.target_file)[1] != ".pptx":
            self.target_file += ".pptx"

        if isfile(self.target_file) and not self.overwrite_file_if_exists:
            msg = "Target description file path specified already exists" \
                  ": {}. Move the file or select the 'overwrite' checkbox."
            msg = msg.format(self.target_file)
            logger.exception(msg)
            raise IOError(msg)

        presentation = Presentation()
        title_slide(presentation, title_text=self.presentation_title,
                    sub_title_text=self.presentation_subtitle)
        img_path = mkstemp()[1] + ".png"

        for i, desc in enumerate(plot_list):
            if self.skip_hidden and not desc.visible:
                continue

            save_plot_to_file(desc.plot, filepath=img_path, dpi=self.image_dpi,
                              **kwargs)
            title = "plot_{}".format(i)
            image_to_slide(presentation, img_path=img_path, slide_title=title)
            os.remove(img_path)

        presentation.save(self.target_file)

    def to_vega(self):
        """ Export plot content to dict (option. file) in Vega-Lite format.

        This is useful to recreate this plotter's content, in a separate
        process, using any plotting library. See the pybleau.reporting for
        tools leveraging this export.

        Returns
        -------
        dict:
            Description of the content of the data plotter.

        TODO: Add filter information for each plot.
        """
        content = {
            CONTENT_KEY: [],
            DATASETS_KEY: {}
        }

        if splitext(self.target_file)[1] != ".json":
            self.target_file += ".json"

        export_dir = abspath(dirname(self.target_file))

        if not isdir(export_dir):
            os.makedirs(export_dir)

        if self.export_data != EXPORT_NO:
            df_data = {}
            if self.export_data == EXPORT_SEPARATE:
                df_data[DATA_FILE_KEY] = self.data_filename + self.data_format
                if self.data_format == ".h5":
                    df_data[DATA_FILE_KEY_KEY] = DATA_KEY
                    comp_info = dict(complib="blosc", complevel=9)
                    df_data[DATA_FILE_COMP_KEY] = comp_info
                    self._export_data_source_to_file(export_dir, **comp_info)
                else:
                    self._export_data_source_to_file(export_dir)

            elif self.export_data == EXPORT_IN_FILE:
                df_data[DATA_KEY] = df_to_vega(self.df_plotter.data_source)
                df_data[IDX_NAME_KEY] = self.df_plotter.data_source.index.name
                content[DATASETS_KEY][DEFAULT_DATASET_NAME] = df_data

        for desc in self.df_plotter.contained_plots:
            if self.export_data == EXPORT_INLINE:
                plot_desc = chaco2vega(desc.plot_config,
                                       export_data="inline")
            elif self.export_data == EXPORT_IN_FILE:
                plot_desc = chaco2vega(desc.plot_config,
                                       export_data=DEFAULT_DATASET_NAME)
            else:
                plot_desc = chaco2vega(desc.plot_config, export_data=False)

            content[CONTENT_KEY].append(plot_desc)

        if self.target_file:
            if isfile(self.target_file) and not self.overwrite_file_if_exists:
                msg = f"Target description file path specified already " \
                    f"exists: {self.target_file}. Move the file or select " \
                    f"the 'overwrite' checkbox."
                logger.exception(msg)
                raise IOError(msg)

            json.dump(content, open(self.target_file, "w"),
                      indent=self.json_index)

        return content

    # Private interface -------------------------------------------------------

    def _export_data_source_to_file(self, target, key=DEFAULT_DATASET_NAME,
                                    **kwargs):
        """ Export the plotter's data source to file.

        Parameters
        ----------
        target : str or pd.XlsxWtriter or pd.HDFStore
            Path to the file or folder or store object to write the source data
            to.

        key : str
            Tag for the dataset. Used only for Excel files (sheet name) or HDF5
            (dataset node name).
        """
        data_format = self.data_format

        if isinstance(target, string_types) and isfile(target):
            msg = "Target data file path specified already exists: {}. It " \
                  "will be overwritten!".format(target)
            logger.info(msg)
        elif isinstance(target, string_types) and isdir(target):
            target = join(target, self.data_filename + data_format)

        df = self.df_plotter.data_source
        if data_format == ".csv":
            df.to_csv(target)
        elif data_format == ".xlsx":
            df.to_excel(target, sheet_name=key, **kwargs)
        elif data_format == ".h5":
            df.to_hdf(target, key=key, **kwargs)
        else:
            msg = "Format {} not implemented. Please report this issue."
            msg = msg.format(data_format)
            logger.exception(msg)
            raise NotImplementedError(msg)

        return target

    def _export_plot_data_to_file(self, plot_list, data_path, **kwargs):
        """ Export the plots' PlotData to a file.

        Supported formats include zipped .csv, multi-tab .xlsx and multi-key
        HDF5.

        Parameters
        ----------
        plot_list : list
            List of PlotDescriptor instances, containing the plot whose data
            need to be exported.

        data_path : str
            Path to the data file to be generated.
        """
        data_format = self.data_format

        if not splitext(data_path)[1]:
            data_path += data_format

        if isfile(data_path):
            msg = "Target data path specified already exists: {}. It will be" \
                  " overwritten.".format(data_path)
            logger.warning(msg)

        data_dir = dirname(data_path)

        if data_format == ".xlsx":
            writer = pd.ExcelWriter(data_path)
        elif data_format == ".h5":
            writer = pd.HDFStore(data_path)

        try:
            if data_format == ".csv":
                data_path = join(data_dir,
                                 string2filename(DEFAULT_DATASET_NAME)+".csv")
                self._export_data_source_to_file(target=data_path)
            elif data_format == ".xlsx":
                writer = pd.ExcelWriter(data_path)
                self._export_data_source_to_file(target=writer,
                                                 key=DEFAULT_DATASET_NAME)
            else:
                self._export_data_source_to_file(target=writer,
                                                 key=DEFAULT_DATASET_NAME)

            created_csv_files = [data_path]
            for i, desc in enumerate(plot_list):
                df_dict = plot_data2dataframes(desc)
                for name, df in df_dict.items():
                    key = "plot_{}_{}".format(i, name)
                    if data_format == ".csv":
                        target_fpath = join(data_dir,
                                            string2filename(key)+".csv")
                        df.to_csv(target_fpath)
                        created_csv_files.append(target_fpath)
                    elif data_format == ".xlsx":
                        df.to_excel(writer, sheet_name=key, **kwargs)
                    elif data_format == ".h5":
                        df.to_hdf(data_path, key=key, **kwargs)
                    else:
                        msg = "Data format {} not implemented. Please report" \
                              " this issue.".format(data_format)
                        logger.exception(msg)
                        raise NotImplementedError(msg)
        finally:
            if data_format in [".xlsx", ".h5"]:
                writer.close()

        if data_format == ".csv" and len(created_csv_files) > 1:
            # zip up all csv files:
            data_path = join(data_dir, self.data_filename + ".zip")
            with ZipFile(data_path, "w") as f:
                for f_path in created_csv_files:
                    f.write(f_path, basename(f_path))

            for f_path in created_csv_files:
                os.remove(f_path)

        if self.interactive:
            msg = "Plot data is stored in: {}".format(data_path)
            information(None, msg)

    # Property getters/setters ------------------------------------------------

    @cached_property
    def _get__export_data_options(self):
        if self.export_format in {IMG_FORMAT, PPT_FORMAT}:
            return [EXPORT_NO, EXPORT_YES]
        elif self.export_format == VEGA_FORMAT:
            return [EXPORT_NO, EXPORT_SEPARATE, EXPORT_IN_FILE,
                    EXPORT_INLINE]
        else:
            msg = "List of export data options not set for format {}."
            msg = msg.format(self.export_format)
            logger.exception(msg)
            raise NotImplementedError(msg)

    # Traits initialization methods -------------------------------------------

    def _target_file_default(self):
        return join(self.target_dir, DEFAULT_EXPORT_FILENAME)

    def _target_dir_default(self):
        return expanduser("~")

    def __many_plots_default(self):
        return len(self.df_plotter.contained_plots) >= 3
