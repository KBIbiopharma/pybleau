
.. _package_overview:

****************
Package Overview
****************


An App for custom exploration of tabular data
---------------------------------------------
The `app` submodule of the project compose a desktop application providing
analysts a limited but coherent set of tools enabling the following
capabilities:
  * viewing the tabular data, sorting, shuffling and filtering it,
    ![tabular view](images/tabular_view.png)
  * viewing a customizable statistical summary of each column (bottom portion
    of the screenshot above),
  * generating polished plots with a graphical interface accessible to anyone,
    ![data_selection](images/data_selection.png)
    ![plot_style_controls](images/plot_style_controls.png)
  * plotting columns as line plots, bar plots, scatter plots, histograms
    (binned frequencies), and heatmaps,
    ![colored_plots](images/colored_plots.png)
  * viewing any number of plots at once, organizing them freely to build a
    coherent story from the data.
  * creating and "freezing" plots for a given portion of the data obtained by
    filtering,
  * displaying any number of dimensions in a scatter plot by using the color
    dimension and hover tools,
  * selecting rows in the data table which triggers point selection in every
    scatter plots and vice-versa,
    ![connected plots](images/connected_plots.png)

In addition to the `pybleau_app` entry point to launch the application, an
example script launching the application on some data can be found in
`scripts/explore_dataframe.py`. Users looking for more built-in customizations
and controls should review `pybleau/app/ui/dataframe_analyzer_model_view.py`.

An app? Yes, but embeddable ETS components too
----------------------------------------------
Despite its name, the `app` submodule is designed to be used as Chaco/Trait
application components, to be embedded into any ETS-based application, no matter the
industry or purpose. Its highest level class is the `DataFrameAnalyzerView` which can
be launched as a top level application (in addition to being embedded in another
tool)::

  >>> from pybleau.app.api import DataFrameAnalyzer, DataFrameAnalyzerView
  >>> import pandas as pd
  >>> data = pd.DataFrame({"A": [1, 2, 3], "B": [3, 2, 3], "C": list("abc")})
  >>> app = DataFrameAnalyzerView(model=DataFrameAnalyzer(source_df=data))
  >>> app.configure_traits()

In this tool, users can then filter or sort data, view its summary change live as
filtering changes. Users can also plot any and multiple parts of it to build an
analysis, before exporting that analysis to json. Since all plots are connected to a
single DataFrame, selecting data in 1 plot triggers a selection in the table view and
all existing plots. Additionally, the plotted data is the filtered data. Changing the
filter will therefore trigger an update of all plots that haven't been set as "frozen".

Additionally developers familiar with ETS can reuse lower level components as they
see fit, such as the `DataFramePlotManager`, its view class, or the configurators and
factories for each type of plot supported.

A functional API to build interactive Plotly plots
--------------------------------------------------

[Note: since this was created, a similar but more complete project has come
 out: https://plot.ly/python/plotly-express/ which is recommended over this.]

The `plotly_api` submodule is designed as an API to build plotly plots
blending matplotlib-style function names, and seaborn-style syntax (provide a
dataframe, and column names for each dimension of the plot). For example, a
colored 2D scatter plot with hover capabilities is built with::

  >>> from pybleau.plotly_api.api import plotly_scatter
  >>> import pandas as pd
  >>> data = pd.DataFrame({"A": [1, 2, 3], "B": [3, 2, 3], "C": list("abc")})
  >>> plotly_scatter(x="A", y="B", data=data, hue="C", hover=["index", "A", "B"])


The same function can also build 3D scatter plots (with coloring and
hovering)::

  >>> plotly_scatter(x="e", y="c", z="d", data=data, hue="a", hover="index")

![3D scatter](images/3d_scatter_plotly.png)

Supported types:
  * 2D scatter plots (dimensions along x, y, z, hue, hover)
  * 3D scatter plots (dimensions along x, y, z, hue, hover)
  * bar plots (multiple dimensions along y/hue)
  * histogram plots (dimensions along x/hue)


For a complete set of examples using the `plotly_api`, refer to
`scripts/plotly_api_visual_tests.ipynb`.

In the long run, the purpose is to provide a functional and unified way to
build interactive plots using different backends in the future without knowing
each package's internals in particular plotly in the notebook and chaco in ETS
desktop apps. So you should expect a `chaco_api` subpackage at some point to
provide a functional entry point to Chaco.
