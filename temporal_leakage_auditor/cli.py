"""Command-line entry point; streams are injectable for process-free tests."""

import argparse
import sys

from . import __version__
from .core import audit_rows
from .inputs import InputError, load_rows, parse_timestamp
from .reports import make_report, render_json, render_markdown


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError("invalid arguments; use --help")


class InformationRequested(Exception):
    pass


class HelpAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        raise InformationRequested(parser.format_help())


class VersionAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        raise InformationRequested(__version__ + "\n")


def close_failed_default_stream(stream):
    if stream is sys.stdout or stream is sys.stderr:
        try:
            stream.close()
        except (OSError, UnicodeError, ValueError):
            pass


def report_error(stderr, message):
    try:
        stderr.write("error: " + message + "\n")
        stderr.flush()
    except (OSError, UnicodeError, ValueError):
        close_failed_default_stream(stderr)
    return 2


def write_output(stdout, stderr, text):
    try:
        stdout.write(text)
        stdout.flush()
    except (OSError, UnicodeError, ValueError):
        # Prevent shutdown from retrying a failed default buffer. Injected
        # caller-owned streams remain the caller's responsibility.
        close_failed_default_stream(stdout)
        return report_error(stderr, "output stream is unavailable")
    return 0


def main(argv=None, stdout=None, stderr=None):
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    parser = Parser(description="Audit declared temporal leakage in CSV/JSON splits.",
                    allow_abbrev=False, add_help=False)
    parser.add_argument("input", metavar="INPUT", help="UTF-8 input file")
    parser.add_argument("--cutoff", required=True, help="explicit UTC validation cutoff")
    parser.add_argument("--input-format", required=True, choices=("csv", "json"))
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("-h", "--help", nargs=0, action=HelpAction,
                        help="show this help message and exit")
    parser.add_argument("--version", nargs=0, action=VersionAction,
                        help="show the version and exit")
    try:
        args = parser.parse_args(argv)
        cutoff, canonical = parse_timestamp(args.cutoff)
        rows = load_rows(args.input, args.input_format, cutoff)
        findings = audit_rows(rows, cutoff)
        report = make_report(rows, canonical, findings)
        text = render_json(report) if args.format == "json" else render_markdown(report)
    except InformationRequested as information:
        return write_output(stdout, stderr, str(information))
    except InputError as error:
        return report_error(stderr, str(error))
    if write_output(stdout, stderr, text):
        return 2
    return 1 if findings else 0
