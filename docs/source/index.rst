.. pybleau documentation master file, created by
   sphinx-quickstart on Thu Oct 22 09:10:35 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Pybleau |version|
=================


.. _whatispybleau:

What is pybleau?
----------------
This repo's name is inspired by the `tableau` data exploration platform and its
purpose is to interactively explore and visualize Pandas dataframes and explore
these explorations. It provides a desktop application (or embeddable desktop
app components) for interactive data exploration and export capabilities to
build simple and interactive reports.

It contains 2 parts. The `app` sub-module contains reusable components for
desktop data exploration using the Enthought Tool Suite (TraitsUI, Chaco, ...,
see http://code.enthought.com/). An analysis can be exported from the desktop
app using a json file using the Vega-Lite format, and converted to reports in
various formats (Dash, ...) using the `reporting` submodule. For now, it only
contains tools to build web-based visualization reports using Plotly/Dash. To
support these translations, `vega_translators` contains utilities to translate
plots and translate it into plotly or Chaco plots.

The project provides 2 entry-points for high-level tools it contains:
  - `pybleau_app` to launch the desktop DF exploration application
  - `pybleau_report` to create a report from a json analysis description file.


.. _project_stage:

Project stage
-------------
Though used in production by multiple projects, this project is still under
active development, in pre-1.0 stage, and may therefore occasionally break
backward compatibility. Minor version number will be bumped when that's the
case. Refer to the changelog for details.

.. _contributor_list:


Project contributors
--------------------

- Jason Chambless
- Jonathan Rocher


.. _table_of_content:

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Last updated on |today|.
