#
#  Copyright (c) 2017, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in enthought/LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
"""
Tasks for Test Runs
===================

This file is intended to be used with a python environment with the
click library to automate the process of setting up test environments
and running the test within them.  This improves repeatability and
reliability of tests be removing many of the variables around the
developer's particular Python environment.  Test environment setup and
package management is performed using `EDM
<http://docs.enthought.com/edm/>`_

To use this to run you tests, you will need to install EDM and click
into your working environment.  You will also need to have git
installed to access required source code from github repositories.
You can then do::

    python etstool.py install --runtime=... --toolkit=...

to create a test environment from the current codebase and::

    python etstool.py test --runtime=... --toolkit=...

to run tests in that environment.  You can remove the environment with::

    python etstool.py cleanup --runtime=... --toolkit=...

If you make changes you will either need to remove and re-install the
environment or manually update the environment using ``edm``, as
the install performs a ``python setup.py install`` rather than a ``develop``,
so changes in your code will not be automatically mirrored in the test
environment.  You can update with a command like::

    edm run --environment ... -- python setup.py install

You can run all three tasks at once with::

    python etstool.py test_clean --runtime=... --toolkit=...

which will create, install, run tests, and then clean-up the environment.  And
you can run tests in all supported runtimes and toolkits (with cleanup)
using::

    python etstool.py test_all

Currently supported runtime values are ``3.5`` and ``3.6``, and currently
supported toolkits are ``null``, ``pyqt``, ``pyqt5``, ``pyside`` and ``wx``.
Not all combinations of toolkits and runtimes will work, but the tasks will
fail with a clear error if that is the case.

Tests can still be run via the usual means in other environments if that suits
a developer's purpose.

Changing This File
------------------

To change the packages installed during a test run, change the dependencies
variable below.  To install a package from github, or one which is not yet
available via EDM, add it to the `ci-src-requirements.txt` file (these will be
installed by `pip`).

Other changes to commands should be a straightforward change to the listed
commands for each task. See the EDM documentation for more information about
how to run commands within an EDM enviornment.

"""

import glob
import os
import subprocess
import sys
import json
from shutil import rmtree, copy as copyfile
from tempfile import mkdtemp
from contextlib import contextmanager

import click

PKG_NAME = "pybleau"

supported_combinations = {
    '3.6': {'pyqt5'},
}

# Default Python version to use in the commands below if none is specified.
DEFAULT_RUNTIME = '3.6'

# Default toolkit to use if none specified.
DEFAULT_TOOLKIT = 'pyqt5'

DEPENDENCIES = "ci/requirements.json"
DEV_DEPENDENCIES = "ci/dev_requirements.json"
PIP_DEPENDENCIES = "ci/pip_requirements.json"

dependencies = set(json.load(open(DEPENDENCIES)) +
                   json.load(open(DEV_DEPENDENCIES)))

# Remove app_common to always test pybleau with app_common master:
for dep in dependencies:
    if dep.startswith("app_common"):
        dependencies = dependencies - {dep}
        break

source_dependencies = {
    "app_common": "git+https://github.com/KBIbiopharma/app_common#egg=app_common",
}

if os.path.isfile(PIP_DEPENDENCIES):
    pip_dependencies = json.load(open(PIP_DEPENDENCIES))
else:
    pip_dependencies = []

# Additional toolkit-independent dependencies
test_dependencies = set()

# Additional toolkit-dependent dependencies
extra_dependencies = {
    # XXX once pyside2 is available in EDM, we will want it here
    'pyside2': set(),
    'pyqt5': {'pyqt5'},
    # XXX once wx is available in EDM, we will want it here
    'wx': set(),
}

runtime_dependencies = {}

doc_dependencies = {
    "sphinx",
    "enthought_sphinx_theme",
}

environment_vars = {
    'pyside2': {'ETS_TOOLKIT': 'qt4', 'QT_API': 'pyside2'},
    'pyqt5': {"ETS_TOOLKIT": "qt4", "QT_API": "pyqt5"},
    'wx': {"ETS_TOOLKIT": "wx"},
}


@click.group()
def cli():
    pass


@cli.command()
@click.option('--runtime', default=DEFAULT_RUNTIME)
@click.option('--toolkit', default=DEFAULT_TOOLKIT)
@click.option('--environment', default=None)
@click.option('--edm-dir', default="")
@click.option(
    "--editable/--not-editable",
    default=False,
    help="Install main package in 'editable' mode?  [default: --not-editable]",
)
def install(runtime, toolkit, environment, edm_dir, editable):
    """ Install project and dependencies into a clean EDM environment.

    Parameters
    ----------
    runtime : str, optional
        Version of Python runtime, e.g. '3.6'.

    toolkit : str, optional
        Name of the GUI toolkit to run the tests for, e.g. 'pyqt5'.

    edm_dir : str, optional
        Path to the edm executable. Useful if the edm executable is not on the
        PATH environment variable.

    environment : str, optional
        Name of the environment to use to execute the command. Leave as None to
        build from the requested runtime and toolkit.
    """
    parameters = get_parameters(runtime, toolkit, environment)
    packages = ' '.join(
        dependencies
        | extra_dependencies.get(toolkit, set())
        | runtime_dependencies.get(runtime, set())
        | test_dependencies
    )
    parameters["edm_dir"] = edm_dir

    # edm commands to setup the development environment
    commands = [
        "{edm_dir}edm environments create {environment} --force "
        "--version={runtime}",
        "{edm_dir}edm install -y -e {environment} " + packages,
        "{edm_dir}edm run -e {environment} -- python setup.py clean --all",
        "{edm_dir}edm run -e {environment} -- pip install -e .",
    ]

    # pip install pyqt5 and pyside2, because we don't have them in EDM yet
    if toolkit == 'pyside2':
        commands.extend([
            "{edm_dir}edm remove -y -e {environment} pyqt5",
            "{edm_dir}edm run -e {environment} -- pip install pyside2==5.11"
        ])
    elif toolkit == 'wx':
        commands.append(
            "{edm_dir}edm remove -y -e {environment} pyqt5 qt"
        )
        if sys.platform != 'linux':
            commands.append(
                "{edm_dir}edm run -e {environment} -- pip install wxPython"
            )
        else:
            # XXX this is mainly for TravisCI workers; need a generic solution
            commands.append(
                "{edm_dir}edm run -e {environment} -- pip install -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-14.04 wxPython"
            )

    click.echo("Creating environment '{environment}'".format(**parameters))
    execute(commands, parameters)

    if source_dependencies:
        # Force remove if it was installed via EDM:
        cmd_fmt = "{edm_dir}edm plumbing remove-package --environment " \
                  "{environment} --force "
        commands = [cmd_fmt+dependency
                    for dependency in source_dependencies.keys()]
        execute(commands, parameters)

        source_pkgs = source_dependencies.values()
        commands = [
            "python -m pip install {pkg} --no-deps".format(pkg=pkg)
            for pkg in source_pkgs
        ]
        commands = ["{edm_dir}edm run -e {environment} -- " + command
                    for command in commands]
        execute(commands, parameters)

    if pip_dependencies:
        commands = [
            "python -m pip install {pkg}".format(pkg=pkg)
            for pkg in pip_dependencies
        ]
        commands = ["{edm_dir}edm run -e {environment} -- " + command
                    for command in commands]
        execute(commands, parameters)

    click.echo('Done install')


@cli.command()
@click.option('--runtime', default=DEFAULT_RUNTIME)
@click.option('--toolkit', default=DEFAULT_TOOLKIT)
@click.option('--edm-dir', default="")
@click.option('--environment', default=None)
@click.option('--cov', default=False, type=bool)
@click.option('--test-pattern', default="")
@click.option('--num-slowest', default="10")
@click.option('--target', default=PKG_NAME)
def test(runtime, toolkit, edm_dir, environment, test_pattern, num_slowest,
         target, cov):
    """ Run test suite (& coverage) in test environment for specified toolkit.

    Parameters
    ----------
    runtime : str, optional
        Version of Python runtime, e.g. '3.6'.

    toolkit : str, optional
        Name of the GUI toolkit to run the tests for, e.g. 'pyqt5'.

    edm_dir : str, optional
        Path to the edm executable. Useful if the edm executable is not on the
        PATH environment variable.

    environment : str, optional
        Name of the environment to use to execute the command. Leave as None to
        build from the requested runtime and toolkit.

    cov : bool, optional
        Whether to compute the test coverage. Defaults to False.

    test_pattern : str, optional
        Pattern of the tests to run. Passed as is to pytest's -m option.

    num_slowest : str, optional
        Number of slowest tests we want to see times for. Defaults to seeing
        all test speeds.

    target : str, optional
        Target package, subpackage, test module, test class or test method to
        run.

    TODO: figure out how to make the test suite run in parallel (with
     '-n auto' option). Currently, parallel execution leads to failures.
    """
    cov_file = ""

    parameters = get_parameters(
        runtime, toolkit, environment, edm_dir=edm_dir, cov_file=cov_file,
        test_pattern=test_pattern, num_slowest=num_slowest, target=target
    )
    environ = environment_vars.get(toolkit, {}).copy()
    environ['PYTHONUNBUFFERED'] = "1"

    if cov:
        commands = [
            "{edm_dir}edm run -e {environment} -- pytest "
            "--cov-config=.coveragerc --durations={num_slowest} "
            "--cov={PKG_NAME} --cov-report=xml:test_coverage.xml "
            "--cov-report=html:test_coverage.html --cov-report term "
            "-m {test_pattern} {target}",
        ]
    else:
        commands = [
            "{edm_dir}edm run -e {environment} -- pytest "
            "--durations={num_slowest} -m {test_pattern} {target}",
        ]

    # We run in a tempdir to avoid accidentally picking up wrong package
    # code from a local dir. We need to ensure a good .coveragerc is in
    # that directory, plus coverage has a bug that means a non-local coverage
    # file doesn't get populated correctly.
    click.echo("Running tests in '{environment}'".format(**parameters))
    os.environ.update(environ)
    execute(commands, parameters)
    click.echo('Done test')


@cli.command()
@click.option('--runtime', default=DEFAULT_RUNTIME)
@click.option('--toolkit', default=DEFAULT_TOOLKIT)
@click.option('--edm-dir', default="")
@click.option('--environment', default=None)
def flake8(runtime, toolkit, edm_dir, environment):
    """ Run flake8 on the source code.

    Parameters
    ----------
    runtime : str, optional
        Version of Python runtime, e.g. '3.6'.

    toolkit : str, optional
        Name of the GUI toolkit to run the tests for, e.g. 'pyqt5'.

    edm_dir : str, optional
        Path to the edm executable. Useful if the edm executable is not on the
        PATH environment variable.

    environment : str, optional
        Name of the environment to use to execute the command. Leave as None to
        build from the requested runtime and toolkit.
    """
    parameters = get_parameters(runtime, toolkit, environment, edm_dir=edm_dir)

    commands = [
        "{edm_dir}edm run -e {environment} flake8 setup.py {PKG_NAME}",
    ]

    execute(commands, parameters)
    click.echo('Done flake8')


@cli.command()
@click.option('--runtime', default=DEFAULT_RUNTIME)
@click.option('--toolkit', default=DEFAULT_TOOLKIT)
@click.option('--edm-dir', default="")
@click.option('--environment', default=None)
def cleanup(runtime, toolkit, edm_dir, environment):
    """ Remove a development environment.

    Parameters
    ----------
    runtime : str, optional
        Version of Python runtime, e.g. '3.6'.

    toolkit : str, optional
        Name of the GUI toolkit to run the tests for, e.g. 'pyqt5'.

    edm_dir : str, optional
        Path to the edm executable. Useful if the edm executable is not on the
        PATH environment variable.

    environment : str, optional
        Name of the environment to use to execute the command. Leave as None to
        build from the requested runtime and toolkit.
    """
    parameters = get_parameters(runtime, toolkit, environment, edm_dir=edm_dir)
    commands = [
        "{edm_dir}edm run -e {environment} -- python setup.py clean",
        "{edm_dir}edm environments remove {environment} --purge -y"]
    click.echo("Cleaning up environment '{environment}'".format(**parameters))
    execute(commands, parameters)
    click.echo('Done cleanup')


@cli.command()
@click.option('--runtime', default=DEFAULT_RUNTIME)
@click.option('--toolkit', default=DEFAULT_TOOLKIT)
def test_clean(runtime, toolkit):
    """ Run tests in a clean environment, cleaning up afterwards.

    Parameters
    ----------
    runtime : str, optional
        Version of Python runtime, e.g. '3.6'.

    toolkit : str, optional
        Name of the GUI toolkit to run the tests for, e.g. 'pyqt5'.
    """
    args = ['--toolkit={}'.format(toolkit), '--runtime={}'.format(runtime)]
    try:
        install(args=args, standalone_mode=False)
        test(args=args, standalone_mode=False)
    finally:
        cleanup(args=args, standalone_mode=False)


@cli.command()
@click.option('--runtime', default=DEFAULT_RUNTIME)
@click.option('--toolkit', default=DEFAULT_TOOLKIT)
@click.option('--edm-dir', default="")
@click.option('--environment', default=None)
def update(runtime, toolkit, edm_dir, environment):
    """ Update/re-install package into environment.

    Parameters
    ----------
    runtime : str, optional
        Version of Python runtime, e.g. '3.6'.

    toolkit : str, optional
        Name of the GUI toolkit to run the tests for, e.g. 'pyqt5'.

    edm_dir : str, optional
        Path to the edm executable. Useful if the edm executable is not on the
        PATH environment variable.

    environment : str, optional
        Name of the environment to use to execute the command. Leave as None to
        build from the requested runtime and toolkit.
    """
    parameters = get_parameters(runtime, toolkit, environment, edm_dir=edm_dir)
    commands = [
        "{edm_dir}edm run -e {environment} -- python setup.py install"]
    click.echo("Re-installing in  '{environment}'".format(**parameters))
    execute(commands, parameters)
    click.echo('Done update')


@cli.command()
@click.option('--runtime', default=DEFAULT_RUNTIME)
@click.option('--toolkit', default=DEFAULT_TOOLKIT)
@click.option('--edm-dir', default="")
@click.option('--environment', default=None)
def docs(runtime, toolkit, edm_dir, environment):
    """ Auto-generate documentation.

    Parameters
    ----------
    runtime : str, optional
        Version of Python runtime, e.g. '3.6'.

    toolkit : str, optional
        Name of the GUI toolkit to run the tests for, e.g. 'pyqt5'.

    edm_dir : str, optional
        Path to the edm executable. Useful if the edm executable is not on the
        PATH environment variable.

    environment : str, optional
        Name of the environment to use to execute the command. Leave as None to
        build from the requested runtime and toolkit.
    """
    parameters = get_parameters(runtime, toolkit, environment, edm_dir=edm_dir)
    packages = ' '.join(doc_dependencies)
    commands = [
        "{edm_dir}edm install -y -e {environment} " + packages,
    ]
    click.echo("Installing documentation tools in  '{environment}'".format(
        **parameters))
    execute(commands, parameters)
    click.echo('Done installing documentation tools')

    os.chdir('docs')
    commands = [
        "{edm_dir}edm run -e {environment} -- make html",
    ]
    click.echo("Building documentation in  '{environment}'".format(**parameters))
    try:
        execute(commands, parameters)
    finally:
        os.chdir('..')
    click.echo('Done building documentation')


@cli.command()
def test_all():
    """ Run test_clean across all supported environment combinations.
    """
    failed_command = False
    for runtime, toolkits in supported_combinations.items():
        for toolkit in toolkits:
            args = [
                '--toolkit={}'.format(toolkit),
                '--runtime={}'.format(runtime)
            ]
            try:
                test_clean(args, standalone_mode=True)
            except SystemExit:
                failed_command = True
    if failed_command:
        sys.exit(1)


# ----------------------------------------------------------------------------
# Utility routines
# ----------------------------------------------------------------------------

def get_parameters(runtime, toolkit, environment, **adtl_params):
    """ Set up parameters dictionary for format() substitution.
    """
    parameters = {'runtime': runtime, 'toolkit': toolkit,
                  'environment': environment, "PKG_NAME": PKG_NAME}
    parameters.update(adtl_params)

    if toolkit not in supported_combinations[runtime]:
        msg = ("Python {runtime} and toolkit {toolkit} not supported by " +
               "test environments")
        raise RuntimeError(msg.format(**parameters))

    if environment is None:
        env_pattern = PKG_NAME + '-develop-{toolkit}-py{runtime}'
        parameters['environment'] = env_pattern.format(**parameters)
        parameters['environment'] = parameters['environment'].replace(".", "")
    return parameters


@contextmanager
def do_in_tempdir(files=(), capture_files=()):
    """ Create a temporary directory, cleaning up after done.

    Creates the temporary directory, and changes into it.  On exit returns to
    original directory and removes temporary dir.

    Parameters
    ----------
    files : sequence of filenames
        Files to be copied across to temporary directory.
    capture_files : sequence of filenames
        Files to be copied back from temporary directory.
    """
    path = mkdtemp()
    old_path = os.getcwd()

    # send across any files we need
    for filepath in files:
        click.echo('copying file to tempdir: {}'.format(filepath))
        copyfile(filepath, path)

    os.chdir(path)
    try:
        yield path
        # retrieve any result files we want
        for pattern in capture_files:
            for filepath in glob.iglob(pattern):
                click.echo('copying file back: {}'.format(filepath))
                copyfile(filepath, old_path)
    finally:
        os.chdir(old_path)
        rmtree(path)


def execute(commands, parameters=None):
    """ Execute command line commands.
    """
    if parameters is None:
        parameters = {}

    for command in commands:
        click.echo("[EXECUTING] {}".format(command.format(**parameters)))
        try:
            subprocess.check_call([arg.format(**parameters)
                                   for arg in command.split()])
        except subprocess.CalledProcessError as exc:
            click.echo(str(exc))
            sys.exit(1)


if __name__ == '__main__':
    cli()
