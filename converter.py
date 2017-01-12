import sys, time, subprocess, json, posixpath, getopt
from os import path, makedirs
import json
import urllib
import requests
import websocket

from logs import logger
from _config import *
# import all available converters
import converters
# import yaml lib for config files
import yaml


# Socket IO Client based on
# https://github.com/invisibleroads/socketIO-client


class Converter(object):
    # the (web)socket over which we'll communicate with the holocloud
    socket = None
    # the class of the converter to be used
    converter_class = 'NoopConverter'
    # the host to conenct to
    host = 'localhost'
    # the port over which to connect
    port = 8000
    # the path at which to connect to the host
    connect_path = 'assets/pipeline/'

    def __init__(self,
                 converter_class=None,
                 host=None,
                 port=None,
                 connect_path=None):
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        if connect_path is not None:
            self.connect_path = connect_path
        if converter_class is not None:
            self.converter_class = converter_class
        # try to instantiate the converter with the available config file
        class_ = getattr(converters, self.converter_class)
        conv_instance = class_()

    def disconnect(self):
        self.socket.off('start-conversion')
        self.socket.disconnect()

    def on_socket_open(self, websocket):
        """
        open / connect handler for websocket connection
        :param websocket: the newly opened websocket instance
        :return:
        """
        logger.info('Now connected to holocloud!')

    def on_socket_message(self, websocket, message):
        """
        message handler for open websocket connection
        :param websocket: the websocket instance on which a message was received
        :param message:
        :return:
        """
        logger.info(message)

    def on_socket_close(self, websocket):
        """
        close handler for open websocket connection
        :param websocket: the websocket instance which was closed
        :return:
        """
        logger.info('Socket closed')

    def on_socket_error(self, websocket, error):
        """
        error handler for open websocket connection
        :param websocket: the websocket instance on which the error ocurred
        :param error:
        :return:
        """
        logger.error(websocket)
        logger.error(error)

    def connect(self, host, port, connect_path):
        """
        connect to the holocloud using (web)sockets
        :param host: the hostname under which holocloud is available
        :param port: the port under which holocloud is available
        :return:
        """
        logger.info('trying to connect to {}:{}'.format(host, port))
        # identify the converter against the host using the converter-type parameter
        self.socket = websocket.WebSocketApp('ws://{}:{}:8000/{}'.format(host, port, connect_path),
                                             on_message=self.on_socket_message,
                                             on_error=self.on_socket_error,
                                             on_close=self.on_socket_close,
                                             on_open=self.on_socket_open)
        # let it run forever
        self.socket.run_forever()

    def on_start_conversion(self, *args):
        # get model id and input path from the received data
        input_data = args[0]
        engine = input_data['engine']
        model_id = input_data['model_id']
        files = input_data['files']
        # only handle requests that match the selected Converter
        if engine == self.converter_class:
            logger.info('starting conversion ...')
            # assert both values exists
            assert model_id, 'No Model ID has been passed'
            assert files, 'No files have been provided'
            # download all the files and move them to a folder of our liking
            download_folder = path.join(TMP_FILES_PATH, 'convertible_{}'.format(model_id))
            output_folder = path.join(download_folder, 'converted')
            if not path.exists(download_folder):
                makedirs(download_folder)
            if not path.exists(output_folder):
                makedirs(output_folder)
            # make sure to remove all files from the tmp download folder first
            for file in files:
                self.download_file_to_be_converted(file, download_folder)
            # convert posix path to whatever system we're on
            input_path = download_folder
            logger.info('now starting conversion progress for file {}'.format(input_path))
            result = self.convert(input_path, output_folder)
            # conversion is done, send the converter-finished event
            # but check if there is a result first
            if result:
                result['engine'] = input_data['engine']
                result['model_id'] = model_id
                if result.get('success', True):
                    logger.info('successfully converted file')
                    logger.info(result)
                    # the model attribute in the result json points to the converted model
                    # now re-upload the converted model to the asset backend
                    self.upload_result(result, output_folder)
                else:
                    logger.warn('failed converting')
                # and finally emit the success method
                self.socket.emit('finish conversion', result)
            else:
                # no result, so conversion appears to have failed
                result = input_data
                del result['files']
                result['success'] = False
                self.socket.emit('finish conversion', result)

    def upload_result(self, result, output):
        url = 'http://{}:{}/{}/{}'.format(self.host, self.port, 'api/models', result['model_id'], result['engine'])
        files = {'file': open(path.join(output, result['model']), 'rb')}
        r = requests.post(url, files=files)
        # should be alright, but if not, raise an exception
        r.raise_for_status()

    def download_file_to_be_converted(self, url, folder):
        testfile = urllib.URLopener()
        testfile.retrieve('http://{}:{}/{}'.format(self.host, self.port, url), path.join(folder, path.basename(url)))

    def convert(self, input_path, output_folder):
        output_path = path.join(CONVERTED_FILES_PATH, output_folder)
        logger.info(
            'starting conversion of files in folder {} and outputting it to {}'.format(
                input_path,
                output_path
            )
        )
        if self.converter_class in self.supported_converters_lut.keys():
            converter_script_path = self.supported_converters_lut.get(self.converter_class)
        else:
            raise NotImplementedError('Converter {} is not supported (yet)'.format(self.converter_class))
        command = 'python {} -i {} -o {}'.format(
            converter_script_path,
            input_path,
            output_path
        )
        logger.info('')
        logger.info(command)
        logger.info('')
        try:
            result = subprocess.check_output(command.split(),
                                             stderr=subprocess.STDOUT,
                                             shell=False)
            # the last line of the output holds the path to the resulting json file
            # which we'll need to inform the backend about all the created files
            lines = result.split('\n')
            result_json = json.loads(lines[len(lines) - 2])
            return result_json
        except subprocess.CalledProcessError as err:
            logger.error(err.output)

    def start(self):
        """
        start this converter and connect it to the holocloud
        :return:
        """
        # first of all, try to connect
        self.connect(self.host, self.port, self.connect_path)


def num(s):
    """
    tries to cast a string to an integer / float value
    :param s:
    :return:
    """
    try:
        return int(s)
    except ValueError:
        return float(s)


USAGE_MESSAGE = 'usage: python {} [-c <converter>][-h <host>][-p <port>][-P <path>]'.format(__file__)


def print_usage():
    print USAGE_MESSAGE


def main(argv):
    # default values
    selected_converter_class = None
    hostname = None
    port = None
    connect_path = None
    # try to read values from config file
    # open the file
    with open('config.yml', 'r') as stream:
        conf = yaml.load(stream)
        print conf
        if conf.get('connection', None) is not None:
            base = conf.get('connection', None)
            hostname = base.get('hostname', hostname)
            port = num(base.get('port', port))
    try:
        opts, args = getopt.getopt(argv, "hc:H:p:P:", ["converter=", "hostname=", "port=", "path="])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ("-c", "--converter"):
            selected_converter_class = arg
        elif opt in ("-H", "--hostname"):
            hostname = arg
        elif opt in ("-p", "--port"):
            port = num(arg)
        elif opt in ("-P", "--path"):
            connect_path = arg
    # create new Converter instance
    # and connect to socket.io server
    converter = Converter(
        converter_class=selected_converter_class,
        host=hostname,
        port=port,
        connect_path=connect_path
    )
    converter.start()


if __name__ == "__main__":
    main(sys.argv[1:])
