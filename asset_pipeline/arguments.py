# coding=utf-8
import argparse
import ConfigParser
import os


def build_parser():
    # We got a 2-step configuration parsing process
    # 1. parse the provided config file (if any) to get some defaults
    # 2. parse the provided command line options which will override the config file settings if applicable
    # ============================
    # Step 1 - Config file parsing
    # ============================
    # We make this parser with add_help=False so that it doesn't parse -h and print help.
    conf_parser = argparse.ArgumentParser()
    conf_parser.add_argument('-c', '--config-file', '--config-path', type=str, metavar='FILE', help=(
        'path to an optional configuration file (configparser format). These settings '
        'allow overriding the connection settings and can provide additional pipeline-'
        'specific settings'
    ))
    # fallback configuration file path (defaults to <current-working-directory>/config.ini
    conf_parser.set_defaults(config_file=os.path.join(os.curdir, 'config.ini'))
    # do a partial parse to only find the configuration file option (if any)
    args, remaining_argv = conf_parser.parse_known_args()

    # default configuration values
    connection_defaults = dict(host='localhost', port=8080, ssl=False)
    # try to read the provided configuration file (or use the fallback configuration file)
    if args.config_file:
        config = ConfigParser.SafeConfigParser()
        config.read([args.config_file])
        # store all values of the config file
        for section in config.sections():
            connection_defaults.update(config.items(section))

    # ================================
    # Step 2 - Parse rest of arguments
    # ================================
    parser = argparse.ArgumentParser(
        description='Process Asset Pipeline configuration arguments.',
        # Don't suppress add_help here so it will handle -h
        add_help=True
    )
    # add optional argument to specify the hostname for a connection
    connection_group = parser.add_argument_group('Connection')
    connection_group.add_argument('-H', '--host', '--hostname', help='hostname at which to connect to the Innoactive Hub®')
    # add optional argument to specify the port for a connection to Innoactive Hub®
    connection_group.add_argument('-P', '--port', type=int, help='port at which to connect to the Innoactive Hub®')
    # add optional argument to specify whether or not to use ssl
    parser.add_argument('-S', '--ssl', dest='ssl', action='store_true', help='whether or not to enforce ssl')
    connection_group.set_defaults(**connection_defaults)
    return parser, remaining_argv


def parse(parser=None, remaining_argv=None):
    if parser is None:
        parser, remaining_argv = build_parser()
    # finally, get all parsed arguments
    return vars(parser.parse_args(remaining_argv))
