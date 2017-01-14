import sys
import getopt
from os import makedirs
import json
import urllib
import requests
import websocket
from logs import logger
from settings import *
# import all available converters
import converters
# import yaml lib for config files
import yaml
from utils import num


class Converter(object):
    # default protocol for downloads is http
    protocol = 'http'
    # the (web)socket over which we'll communicate with the holocloud
    socket = None
    # the class of the converter to be used
    converter_class = 'NoopConverter'
    # the host to conenct to
    host = 'localhost'
    # the port over which to connect
    port = 8000
    # the path at which to connect to the host
    connect_path = 'assets/pipeline'
    # uniquely identying slug of the platform this converter works for
    platform_slug = None
    platform = None
    # the actual instance of the converter doing the heavy lifting
    converter_instance = None

    def __init__(self,
                 converter_class=None,
                 host=None,
                 port=None,
                 connect_path=None,
                 platform_slug=None):
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        if connect_path is not None:
            self.connect_path = connect_path
        if converter_class is not None:
            self.converter_class = converter_class
        if platform_slug is not None:
            self.platform_slug = platform_slug
        # try to instantiate the converter with the available config file
        class_ = getattr(converters, self.converter_class)
        self.converter_instance = class_(platform_slug=self.platform_slug)
        logger.info('Running based on %s' % self.converter_instance)

    def disconnect(self):
        """
        disconnect the open socket
        :return:
        """
        self.socket.disconnect()

    def on_socket_open(self, websocket):
        """
        open / connect handler for websocket connection
        :param websocket: the newly opened websocket instance
        :return:
        """
        logger.info('Successfully connected to holocloud!')

    def on_socket_message(self, websocket, message):
        """
        message handler for open websocket connection
        :param websocket: the websocket instance on which a message was received
        :param message:
        :return:
        """
        # the message should be json, try to parse it now
        msg = json.loads(message)
        # check if a message type is included
        if isinstance(msg, dict):
            # check what kind of message we got
            if 'type' in msg:
                msg_type = msg.get('type')
                if msg_type == MessageType.CONVERSION_START:
                    # the msg needs to contain some data in order to convert anything
                    if 'data' in msg:
                        model = msg.get('data')
                        logger.info('Starting to convert. Model data is %s' % model)
                        self.convert(model)
                    else:
                        logger.warn('Should start converting, but data is missing from message: \n%s' % message)

    def on_socket_close(self, websocket):
        """
        close handler for open websocket connection
        :param websocket: the websocket instance which was closed
        :return:
        """
        logger.info('Connection to Holocloud closed')

    def on_socket_error(self, websocket, error):
        """
        error handler for open websocket connection
        :param websocket: the websocket instance on which the error ocurred
        :param error:
        :return:
        """
        # logger.error(websocket)
        # logger.error(error)
        pass

    def connect(self, host, port, connect_path):
        """
        connect to the holocloud using (web)sockets
        :param connect_path: the path at which to connect to the server (e.g. /websocket/chat)
        :param host: the hostname under which holocloud is available
        :param port: the port under which holocloud is available
        :return:
        """
        logger.info('trying to connect to {}:{}'.format(host, port))
        # identify the converter against the host using the converter-type parameter
        self.socket = websocket.WebSocketApp(
            'ws://{}:{}:8000/{}/{}'.format(host, port, connect_path, self.platform_slug),
            on_message=self.on_socket_message,
            on_error=self.on_socket_error,
            on_close=self.on_socket_close,
            on_open=self.on_socket_open,
            header={
                PLATFORM_SLUG_HEADER: self.platform_slug
            }
        )
        # let it run forever
        self.socket.run_forever()

    def start_conversion_progress(self, model):
        """
        signal to be executed right before file conversion starts
        :return:
        """
        self.socket.send(json.dumps({
            'type': MessageType.CONVERSION_PROGRESS,
            'model_id': model.get('id')
        }))
        # we will need the platform model on which we're working, so try to create it now
        url = '{proto}://{host}:{port}/api/platformmodels/'.format(proto=self.protocol, host=self.host, port=self.port)
        payload = {
            "model": model.get('id'),
            "platform": self.platform['id'],
            "conversion_state": ConversionState.IN_PROGRESS
        }
        response = requests.request("POST", url, json=payload)
        # check if the operation was successful
        if 200 <= response.status_code < 300:
            # parse the response
            return response.json()
        else:
            logger.error('Could not create platform model')
            logger.error(response.text)
            return None

    def finish_conversion_progress(self, platform_model, converted_file_path):
        """
        signal to be executed right after file conversion has ended
        :param converted_file_path: the file path at which the converted file is located
        :param model: the model data
        :return:
        """
        logger.info(
            'Model %s successfully converted. Resulting file is located at %s' % (
                str(platform_model.get('model')), converted_file_path))
        # upload the converted file
        # and update the conversion_progress
        self.upload_conversion_result(platform_model, converted_file_path)

    def convert(self, model):
        """
        makes sure to download files and then use the appropriate converter to convert the provided model
        :param model:
        :return:
        """
        # only handle requests that match the selected Converter
        logger.info('Sarting conversion of model %s ...' % model.get('id'))
        # download all the files and move them to a folder of our liking
        model_working_directory = path.join(TMP_FILES_PATH, str(model.get('id')))
        download_folder = path.join(model_working_directory, 'original')
        output_folder = path.join(model_working_directory, 'converted')
        # make sure the folder exist
        if not path.exists(download_folder):
            makedirs(download_folder)
        if not path.exists(output_folder):
            makedirs(output_folder)
        # download the specified file
        input_path = self.download_file(model.get('upload').get('file'), download_folder)
        # convert posix path to whatever system we're on
        logger.info('now starting conversion progress for file {}'.format(input_path))
        # execute the start_conversion_progress hook
        working_model = self.start_conversion_progress(model)
        if working_model is None:
            logger.error('Could not initialize a suitable Platform Model to work on. Aborting Conversion Process')
        else:
            logger.info(working_model)
            # get the converter instance to do the heavy lifting for us
            converted_file_path = self.converter_instance.convert(input_path, output_folder)
            self.finish_conversion_progress(working_model, converted_file_path)

    def upload_conversion_result(self, platform_model, result_file_path):
        """
        uploads the converted model back to the holocloud
        :param platform_model:
        :param result_file_path:
        :return:
        """
        url = '{proto}://{host}:{port}/{path}/{id}/'.format(proto=self.protocol, host=self.host,
                                                            port=self.port,
                                                            path='api/platformmodels', id=platform_model['id'])
        logger.debug('Uploading file to %s' % url)
        # attach the conversion result as a file to the post request
        # also set the state to finished
        payload = {
            'file': open(result_file_path, 'rb'),
            # the empty string in the tuple will prevent of setting a filename for this non file value
            'conversion_state': ('', ConversionState.FINISHED)
        }
        response = requests.request("PUT", url, files=payload)
        logger.info(response.text)
        # if we get an error, show it.
        response.raise_for_status()

    def download_file(self, _path, folder):
        """
        downloads the file located on the server at _path
        :param _path: the location of the file on the server
        :param folder: download folder
        :return:
        """
        downloader = urllib.URLopener()
        outfile_path = path.join(folder, path.basename(_path))
        url = '{proto}://{host}:{port}{path}'.format(proto=self.protocol, host=self.host, port=self.port, path=_path)
        logger.debug('Downloading file from %s' % url)
        downloader.retrieve(url, outfile_path)
        return outfile_path

    def start(self):
        """
        start this converter and connect it to the holocloud
        :return:
        """
        # first of all, find out details about the platform we're working on. We'll need that one later on
        self.platform = self.retrieve_platform_by_slug(self.platform_slug)
        if self.platform is None:
            logger.error(
                'Could not load platform details for platform {slug}. '
                'Please check if the provided platform slug is correct'.format(
                    slug=self.platform_slug))
        else:
            logger.info('Platform is {}'.format(self.platform))
            self.connect(self.host, self.port, self.connect_path)

    def retrieve_platform_by_slug(self, slug):
        """
        retrieves information about the platform that this converter works for

        identified by the platform_slug
        :param slug:
        :return:
        """
        url = '{proto}://{host}:{port}/api/platforms/slugs/{slug}'.format(proto=self.protocol, host=self.host,
                                                                          port=self.port, slug=slug)
        response = requests.request("GET", url)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            return None

    def stop(self):
        """
        stop this converter and disconnect from holocloud
        :return:
        """
        self.disconnect()


USAGE_MESSAGE = 'usage: python {} [-c <converter>][-h <host>][-p <port>][-P <path>]'.format(__file__)


def print_usage():
    print USAGE_MESSAGE


def main(argv):
    # default values
    selected_converter_class = None
    platform_slug = None
    hostname = None
    port = None
    connect_path = None
    # try to read values from config file
    # open the file
    with open('config.yml', 'r') as stream:
        conf = yaml.load(stream)
        if conf.get('connection', None) is not None:
            base = conf.get('connection', None)
            hostname = base.get('hostname', hostname)
            port = num(base.get('port', port))
        if conf.get('converter', None) is not None:
            base = conf.get('converter', None)
            selected_converter_class = base.get('class', selected_converter_class)
            platform_slug = base.get('slug')
    try:
        opts, args = getopt.getopt(argv, "hc:H:p:P:s:", ["converter=", "hostname=", "port=", "path=", "slug="])
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
        elif opt in ("-s", "--slug"):
            platform_slug = arg
    # create new Converter instance
    # and connect to socket.io server
    converter = Converter(
        converter_class=selected_converter_class,
        host=hostname,
        port=port,
        connect_path=connect_path,
        platform_slug=platform_slug
    )
    converter.start()

if __name__ == "__main__":
    main(sys.argv[1:])
