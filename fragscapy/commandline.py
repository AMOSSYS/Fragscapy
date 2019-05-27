import argparse
import logging
import importlib
import os

from scapy.config import conf

from fragscapy import __author__ as author, __version__ as version
from fragscapy.config import Config
from fragscapy.engine import Engine

PROG_NAME="Fragscapy"
DESCRIPTION = ("Runs a series of tests on the network and modify the packets "
               "on the fly in order to test the behavior of the machines on "
               "the network")
EPILOG = "Fragscapy {version} - {author}".format(version=version, author=author)

def command():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EPILOG, prog=PROG_NAME
    )

    parser.add_argument(
        '-V', '--version',
        action='version',
        version="Fragscapy {version}".format(version=version)
    )

    subparsers = parser.add_subparsers(dest='subcmd')

    # fragscapy list
    parser_list = subparsers.add_parser('list', help="List the available mods")

    # fragscapy usage
    parser_usage = subparsers.add_parser('usage', help="Details the usage of a mod")
    parser_usage.add_argument(
        'mod',
        type=str,
        nargs='+',
        help="The name of a mod to show the usage"
    )

    # fragscapy start
    parser_start = subparsers.add_parser('start', help="Start the tests")
    parser_start.add_argument(
        'config_file',
        type=str,
        metavar='<config file>',
        help="The config file to use"
    )
    parser_start.add_argument(
        '--scapy-output',
        action='store_true',
        help="Enable the standard scapy output for each packet sent"
    )
    parser_start.add_argument(
        '--no-progressbar',
        action='store_true',
        help="Disable the progressbar. Can be useful in non interactive terminals"
    )

    args = parser.parse_args()

    if args.subcmd == 'list':
        list_mods()
    elif args.subcmd == 'usage':
        usage(args)
    elif args.subcmd == 'start':
        start(args)
    else:
        parser.print_help()


def list_mods():
    print("I'm listing the mods")


def start(args):
    print(args.scapy_output)
    if not args.scapy_output:
        # Removes warning messages
        logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
        # Removes verbose send messages
        conf.verb = 0

    config = Config(args.config_file)
    engine = Engine(config, not args.no_progressbar)
    engine.start()


def usage(args):
    print("Usage of:")
    for mod in args.mod:
        print(mod)


if __name__ == '__main__':
    command()
