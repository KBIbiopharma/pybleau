
from __future__ import print_function
import argparse

from app_common.std_lib.logging_utils import initialize_logging


def build_report(report_desc_file, backend="dash", logging_level="DEBUG",
                 report_title="New Report", report_logo="", **kwargs):
    """ Entry point to build and open a new report.
    """
    initialize_logging(logging_level=logging_level)
    if backend == "dash":
        from pybleau.reporting.dash_tools import analysis_file2dash_reporter \
            as build_reporter
    else:
        raise NotImplementedError()

    reporter = build_reporter(report_desc_file, report_title=report_title,
                              report_logo=report_logo, **kwargs)
    reporter.open_report()
    return reporter


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        conflict_handler='resolve',
        description="Data report generator"
    )
    parser.add_argument('-i', '--input',
                        help='Path to the report description file.')
    parser.add_argument('-b', '--backend', default='dash',
                        help="The backend to use. Only value currently "
                             "supported is 'dash'. ")
    parser.add_argument('-t', '--title', default='New Data Report',
                        help="Title of the report")
    parser.add_argument('-l', '--logo', default='',
                        help="Path to the logo file to display at the top of "
                             "the report")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Increase logging output.')
    parser.add_argument('--version', action='store_true',
                        help='Print the program version and exit.')

    args = parser.parse_args()
    if args.version:
        import pybleau
        print(pybleau.__version__)
    else:
        logging_level = "DEBUG" if args.verbose else "WARNING"
        build_report(args.input, report_title=args.title,
                     report_logo=args.logo, backend=args.backend,
                     logging_level=logging_level)


if __name__ == "__main__":
    main()
