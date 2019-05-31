"""Command-line specific operations and parsing.

Handles everything related to the command line and its many options. The main
entry point is `command()` which will parse the arguments from `sys.args` and
triggers the correct function depending on the arguments given.
"""

import argparse
import logging
import traceback

import scapy.config

from fragscapy._author import __author__
from fragscapy._version import __version__
from fragscapy.config import Config
from fragscapy.engine import Engine
from fragscapy.modgenerator import get_all_mods, get_mod


PROG_NAME = "Fragscapy"
DESCRIPTION = ("Runs a series of tests on the network and modify the packets "
               "on the fly in order to test the behavior of the machines on "
               "the network")
EPILOG = "Fragscapy {version} - {author}".format(
    version=__version__, author=__author__)


def command():
    """Parses the arguments from the command line and trigger the action.

    The main sub-commands are:
    * 'list' for listing the mods that can be detected
    * 'usage' for detailling the usage of one (or multiple) mods
    * 'checkconfig' to check various aspects of a configuration file
    * 'start' to run the test suite described by a config file
    """
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EPILOG, prog=PROG_NAME
    )

    parser.add_argument(
        '-V', '--version',
        action='version',
        version="Fragscapy {version}".format(version=__version__)
    )

    subparsers = parser.add_subparsers(dest='subcmd')

    # fragscapy list
    subparsers.add_parser('list', help="List the available mods")

    # fragscapy usage
    parser_usage = subparsers.add_parser('usage', help="Details the usage of a mod")
    parser_usage.add_argument(
        'mod',
        type=str,
        nargs='+',
        help="The name of a mod to show the usage"
    )

    # fragscapy checkconfig
    parser_checkconfig = subparsers.add_parser(
        'checkconfig',
        help="Parse and check a config file without running the test suite"
    )
    parser_checkconfig.add_argument(
        'config_file',
        type=str,
        metavar='<config_file>',
        help="The config file to use"
    )
    parser_checkconfig.add_argument(
        '--modif-file',
        type=str,
        metavar='<modif_file>',
        help="Where to write the modifications, default is 'modifications.txt'"
    )
    parser_checkconfig.add_argument(
        '--traceback', '--tb',
        action='store_true',
        help="Show the traceback when an error occurs"
    )
    parser_checkconfig.add_argument(
        '--no-progressbar',
        action='store_true',
        help="Disable the progressbar. Can be useful in non interactive terminals"
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
        '--modif-file',
        type=str,
        metavar='<modif_file>',
        help="Where to write the modifications, default is 'modifications.txt'"
    )
    parser_start.add_argument(
        '--stdout-file',
        type=str,
        metavar='<stdout_file>',
        help="Where to redirect stdout, default is 'stdout{i}.txt'"
    )
    parser_start.add_argument(
        '--stderr-file',
        type=str,
        metavar='<stderr_file>',
        help="Where to redirect stderr, default is 'stderr{i}.txt'"
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
    elif args.subcmd == 'checkconfig':
        checkconfig(args)
    elif args.subcmd == 'start':
        start(args)
    else:
        parser.print_usage()


def list_mods():
    """Lists all the mods that can be detected."""
    all_mods_name = sorted(map(
        lambda x: x.name or x.__class__.__name__.lower(),
        get_all_mods()
    ))
    print("Found {} available mods:".format(len(all_mods_name)))
    for mod in all_mods_name:
        print("  - {}".format(mod))


def start(args):
    """Runs the test suite.

    Args:
        args: The arguments found in the `argparse.ArgumentParser`
    """
    if not args.scapy_output:
        # Removes warning messages
        logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
        # Removes verbose send messages
        scapy.config.conf.verb = 0

    config = Config(args.config_file)
    kwargs = _filter_kwargs(args, ['modif_file', 'stdout_file', 'stderr_file'])
    engine = Engine(config, progressbar=(not args.no_progressbar), **kwargs)
    engine.start()


def usage(args):
    """Prints the usage for specific mods.

    Args:
        args: The arguments found in the `argparse.ArgumentParser`
    """
    for mod_name in args.mod:
        try:
            mod = get_mod(mod_name)
            mod.usage()
            print("")
        except ModuleNotFoundError:
            print("Unknown modification: '{}'".format(mod_name))


def checkconfig(args):
    """Checks that the config file looks correct.

    It does not guarantee that there will be no crash during the test suite
    but it tries to catch everything before running it.

    Args:
        args: The arguments found in the `argparse.ArgumentParser`
    """
    try:
        print(">>> Loading config file")
        config = Config(args.config_file)
        print(">>> Loading engine")
        kwargs = _filter_kwargs(args, ['modif_file'])
        engine = Engine(config, progressbar=(not args.no_progressbar), **kwargs)
        print(">>> Checking Netfilter rules")
        engine.check_nfrules()
        print(">>> Checking mod list generation (output to '{}')"
              .format(args.modif_file))
        engine.check_modlist_generation()
    except BaseException as e:  # pylint: disable=broad-except
        if args.traceback:
            traceback.print_tb(e.__traceback__)
        print("{name}: {msg}".format(name=e.__class__.__name__, msg=e))


def _filter_kwargs(args, keys):
    """Filters and transforms argparse's args to a kwargs.

    Args:
        args: The arguments found in the `argparse.ArgumentParser`
        keys: The keys to keep
    """
    kwargs = dict()
    for k in keys:
        if hasattr(args, k) and getattr(args, k) is not None:
            kwargs[k] = getattr(args, k)
    return kwargs


if __name__ == '__main__':
    command()
