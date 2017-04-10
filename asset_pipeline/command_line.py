import getopt
import sys

import yaml

from pipeline import NoopRemoteAssetPipeline
from utils import num

USAGE_MESSAGE = 'usage: python {} [-H <host>][-P <port>][-c <config>]'.format(__file__)


def print_usage():
    print USAGE_MESSAGE


def main(argv):
    # default values
    hostname = None
    port = None
    # try to read values from config file
    config_file_path = 'config.yml'
    # also check if an alternative config file path has been provided
    try:
        opts, args = getopt.getopt(argv, "hc:", ["config="])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ("-c", "--config"):
            config_file_path = arg
    # open the file
    with open(config_file_path, 'r') as stream:
        config = yaml.load(stream)
        if config.get('connection', None) is not None:
            base = config.get('connection', None)
            hostname = base.get('hostname', hostname)
            port = num(base.get('port', port))
    try:
        opts, args = getopt.getopt(argv, "hH:c:p:P:", ["config=", "hostname=", "port="])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ("-H", "--hostname"):
            hostname = arg
        elif opt in ("-P", "-p", "--port"):
            port = num(arg)
    # create new RemoteAssetPipeline instance
    # and connect to socket.io server
    asset_pipeline = NoopRemoteAssetPipeline(
        host=hostname,
        port=port,
        config=config
    )
    asset_pipeline.start()


if __name__ == "__main__":
    main(sys.argv[1:])
