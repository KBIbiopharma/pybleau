from unittest import TestCase
from pandas import DataFrame
import os
from os.path import isfile

from pybleau.app.api import main


class TestLaunchMainApp(TestCase):
    def setUp(self):
        self.df = DataFrame({"a": range(4), "b": list("abcd")})
        self.filename = "temp"

    def tearDown(self):
        if isfile(self.filename):
            os.remove(self.filename)

    def test_launch_app_around_df_default(self):
        main(target=self.df, ui_kind=None)

    def test_launch_app_around_df_include_plotter(self):
        main(target=self.df, ui_kind=None, include_plotter=True)

    def test_launch_app_around_df_control_plotter_layout(self):
        main(target=self.df, ui_kind=None, include_plotter=True,
             plotter_layout="HSplit")

        main(target=self.df, ui_kind=None, include_plotter=True,
             plotter_layout="Tabbed")

    def test_launch_app_around_csv_file(self):
        self.filename += ".csv"
        self.df.to_csv(self.filename)
        main(target=self.filename, ui_kind=None)

    def test_launch_app_around_excel_file(self):
        self.filename += ".xls"
        self.df.to_excel(self.filename)
        main(target=self.filename, ui_kind=None)

    def test_launch_app_around_excel2_file(self):
        self.filename += ".xlsx"
        self.df.to_excel(self.filename)
        main(target=self.filename, ui_kind=None)

    def test_launch_app_around_excel2_file_custom_sheet(self):
        self.filename += ".xlsx"
        self.df.to_excel(self.filename, sheet_name="foo")
        main(target=self.filename, ui_kind=None,
             read_func_kw={"sheet_name": "foo"})

    def test_launch_app_around_hdf_file(self):
        self.filename += ".h5"
        self.df.to_hdf(self.filename, key="data")
        main(target=self.filename, ui_kind=None, read_func_kw={"key": "data"})

    def test_launch_app_around_hdf_file2(self):
        self.filename += ".hdf"
        self.df.to_hdf(self.filename, key="data")
        main(target=self.filename, ui_kind=None, read_func_kw={"key": "data"})
