# coding=utf-8
import json
import shutil
import urllib
from distutils.dir_util import copy_tree
from os import makedirs

import requests
import sys
import websocket

from logger import logger
from protocol import *


class AbstractAssetPipeline(object):
    """
    base asset pipeline implementation from which all pipelines are to be derived
    """
    # list of filetypes this converter can handle
    supported_filetypes = []

    # asset pipeline configuration provided as a dictionary
    config = None

    def __init__(self, config=None):
        """
        public constructor / main initialization method
        :param config:
        """
        if config is not None:
            # validate the configuration
            if self.validate_configuration(config):
                self.config = config
            else:
                raise AttributeError('The provided configuration could not be validated. Please verify!')

    def validate_configuration(self, config):
        """
        validates the given configuration with respect to the converter instance
        :param config:
        :return:
        """
        raise NotImplementedError('Subclasses of the AbstractAssetPipeline must implement the validate_configuration method')

    def supports(self, input_file):
        """
        simple method to check whether this converter supports the given file
        :param input_file: the file to be converted (potentially)
        :return:
        """
        return path.split(input_file)[1] in self.supported_filetypes

    def run(self, asset_data):
        """
        runs the pipeline through by executing (in this order):
        - pre_execute
        - execute
        - post_execute
        :return:
        """
        self.pre_execute(asset_data)
        self.execute(asset_data)
        self.post_execute(asset_data)

    def execute(self, asset_data):
        """
        converts the given input file to be compatible with the specified platform
        :param asset_data:
        :return:
        """
        raise NotImplementedError('Subclasses of the AbstractAssetPipeline must implement the execute method')

    def pre_execute(self, asset_data):
        """
        executed before the actual pipeline is processed
        :param asset_data:
        :return:
        """
        raise NotImplementedError('Subclasses of the AbstractAssetPipeline must implement the pre_execute method')

    def post_execute(self, asset_data):
        """
        executed after the actual pipeline has been processed
        :param asset_data:
        :return:
        """
        raise NotImplementedError('Subclasses of the AbstractAssetPipeline must implement the post_execute method')

    def supports(self, asset_data):
        """
        simple method to check whether this pipeline supports the given file
        :param asset_data: all available data about the asset to be converted
        :return:
        """
        # get the filename of the asset to be handled
        input_file = asset_data.get('upload', {}).get('file')
        return path.split(input_file)[1] in self.supported_filetypes

    def __str__(self):
        return '%s' % self.__class__.__name__


class BaseRemoteAssetPipeline(AbstractAssetPipeline):
    """
    remotely triggered asset pipeline. Will receive working instructions via an established websocket connection
    """
    # default protocol for downloads is http
    protocol = 'http'
    # the (web)socket over which we'll communicate with the holocloud®
    socket = None
    # the host to connect to
    host = 'localhost'
    # the port over which to connect
    port = 8000
    # the path at which to connect to the host for working packages
    connect_path = 'assets/pipeline/'
    # dictionary of additional headers to be included in an connection attempt
    additional_headers = {}

    def __init__(self,
                 config=None,
                 *args,
                 **kwargs):
        # call parent constructor (taking care of config validation)
        super(BaseRemoteAssetPipeline, self).__init__(config=config, *args, **kwargs)
        # update host and port values
        self.host = config['host']
        self.port = config['port']
        logger.info('Running based on %s' % self)

    def validate_configuration(self, config):
        # make sure hostname and port are set
        if 'host' not in config:
            logger.error("Hostname needs to be provided in order to connect the pipeline to the holocloud®")
            return False
        if 'port' not in config:
            logger.error("Port needs to be provided in order to connect the pipeline to the holocloud®")
            return False
        # if we got here, everything's fine
        return True

    @staticmethod
    def on_socket_open(socket):
        """
        open / connect handler for websocket connection
        :param socket: the newly opened websocket instance
        :return:
        """
        logger.info('Successfully connected to holocloud®!')

    @staticmethod
    def on_socket_close(socket):
        """
        close handler for open websocket connection
        :param socket: the websocket instance which was closed
        :return:
        """
        logger.info('Connection to holocloud® closed')

    @staticmethod
    def on_socket_error(socket, error):
        """
        error handler for open websocket connection
        :param socket: the websocket instance on which the error ocurred
        :param error:
        :return:
        """
        logger.error(socket)
        logger.error(error)

    def on_socket_message(self, socket, message):
        """
        message handler for open websocket connection
        :param socket: the websocket instance on which a message was received
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
                    # the msg needs to contain some data in order to execute anything
                    if 'data' in msg:
                        asset_data = msg.get('data')
                        logger.info('Starting to run pipeline... Model data is %s' % asset_data)
                        if self.supports(asset_data):
                            self.run(asset_data)
                        else:
                            logger.info("Could not handle provided asset %s" % asset_data)
                    else:
                        logger.warn('Should start converting, but data is missing from message: \n%s' % message)

    def pre_execute(self, asset_data):
        """
        signal to be executed right before file conversion starts
        :return:
        """
        logger.info("Running pre-pipeline hook for asset_data %s" % asset_data)
        # download all the asset's files and move them to a folder of our liking
        model_working_directory = path.join(TMP_FILES_PATH, str(asset_data.get('id')))
        download_folder = path.join(model_working_directory, 'original')
        output_folder = path.join(model_working_directory, 'converted')
        # make sure the folder exist
        if not path.exists(download_folder):
            makedirs(download_folder)
        if not path.exists(output_folder):
            makedirs(output_folder)
        # download the specified file
        input_path = self.download_file(asset_data.get('upload').get('file'), download_folder)
        # store the input file path inside the asset_data for later usage
        if 'input' not in asset_data:
            asset_data['input'] = {}
        asset_data['input']['path'] = input_path
        # also store the directory to which we'll output the converted files
        if 'output' not in asset_data:
            asset_data['output'] = {}
        asset_data['output']['path'] = output_folder
        return asset_data

    def execute(self, asset_data):
        logger.info("Running pipeline for asset_data %s" % asset_data)
        return asset_data

    def post_execute(self, asset_data):
        """
        signal to be executed right after file conversion has ended
        :param asset_data: the asset's data + any working data created during the pipeline process
        :return:
        """
        logger.info("Running post-pipeline hook for asset_data %s" % asset_data)
        return asset_data

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
        start this asset pipeline and connect it to the holocloud® to listen for updates / working instructions
        :return:
        """
        logger.info('trying to connect to {}:{}'.format(self.host, self.port))
        # identify the converter against the host using the converter-type parameter
        self.socket = websocket.WebSocketApp(
            'ws://{}:{}/{}'.format(self.host, self.port, self.connect_path),
            on_message=self.on_socket_message,
            on_error=self.on_socket_error,
            on_close=self.on_socket_close,
            on_open=self.on_socket_open,
            header=self.additional_headers
        )
        # let it run forever
        self.socket.run_forever()

    def stop(self):
        """
        stop this converter and disconnect from holocloud
        :return:
        """
        self.socket.close()


class PlatformSpecificAssetPipelineMixin(object):
    """
    Mixin used for asset pipelines that are specific to one platform
    requires an additional and unique platform_slug to be provided
    """
    # uniquely identifying slug of the platform this converter works for
    platform_slug = None
    platform = None
    # dictionary of additional headers to be included in an connection attempt
    additional_headers = {
        PLATFORM_SLUG_HEADER: 'unknown'
    }

    def __init__(self,
                 config=None,
                 *args,
                 **kwargs):
        # call parent constructor (taking care of config validation)
        super(PlatformSpecificAssetPipelineMixin, self).__init__(config=config, *args, **kwargs)
        # handle the platform slug parameter
        if 'platform_slug' in config:
            self.platform_slug = config['platform_slug']
        else:
            logger.warn("No Platform Slug provided. Platform Specific pipeline will probably not work.")
        # store the platform slug in the list of additional headers
        self.additional_headers['PLATFORM_SLUG_HEADER'] = self.platform_slug

    def pre_execute(self, asset_data):
        # execute parent logic
        asset_data = super(PlatformSpecificAssetPipelineMixin, self).pre_execute(asset_data)
        # we will need the platform-specific asset_data on which we're working, so try to create it now
        url = '{proto}://{host}:{port}/api/platformmodels/'.format(proto=self.protocol, host=self.host, port=self.port)
        payload = {
            "model": asset_data.get('id'),
            "platform": self.platform['id'],
            "conversion_state": ConversionState.IN_PROGRESS
        }
        response = requests.request("POST", url, json=payload)
        # check if the operation was successful
        if 200 <= response.status_code < 300:
            # parse the response
            platform_asset_data = response.json()
            # store the platform specific asset data
            asset_data['platform_specific'] = platform_asset_data
        else:
            logger.error('Could not create platform asset_data')
            logger.error(response.text)
        return asset_data

    def start(self):
        """
        start this asset pipeline and connect it to the holocloud® to listen for updates / working instructions
        also, find out platform data before proceeding
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
            # proceed with the default implementation
            super(PlatformSpecificAssetPipelineMixin, self).start()

    def retrieve_platform_by_slug(self, slug):
        """
        retrieves information about the platform that this converter works for

        identified by the platform_slug
        :param slug:
        :return:
        """
        url = '{protocol}://{host}:{port}/api/platforms/slugs/{slug}'.format(protocol=self.protocol, host=self.host,
                                                                             port=self.port, slug=slug)
        response = requests.request("GET", url)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            return None


class NoopRemoteAssetPipeline(BaseRemoteAssetPipeline):
    def validate_configuration(self, config):
        return True

    def execute(self, asset_data):
        super(NoopRemoteAssetPipeline, self).execute(asset_data)
        output_folder = asset_data.get('output', {}).get('path', None)
        input_file = asset_data.get('input', {}).get('path', None)
        # clean up before starting
        # clear all files from the output_folder
        # to do so, just delete the entire folder
        if path.exists(output_folder):
            shutil.rmtree(output_folder)
        # ... and recreate it afterwards
        makedirs(output_folder)
        # start copying everything from the input_file's folder to the output folder
        from_dir = path.dirname(input_file)
        to_dir = output_folder
        copy_tree(from_dir, to_dir)
        # return the path to the "converted" file
        return asset_data
