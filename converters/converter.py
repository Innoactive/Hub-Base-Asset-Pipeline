import os
import shutil
from distutils.dir_util import copy_tree
from os import path


class AbstractConverter(object):
    """
    list of filetypes this converter can handle
    """
    supported_filetypes = []

    """
    configuration options
    """
    config = None

    """
    the uniquely identifying slug for the platform that this converter works for
    """
    platform_slug = None

    def __init__(self, config=None):
        if config is not None:
            # validate the configuration
            if self.validate_configuration(config):
                self.config = config
            else:
                raise AttributeError('The provided configuration could not be validated. Please verify')

    def validate_configuration(self, config):
        """
        validates the given configuration with respect to the converter instance
        :param config:
        :return:
        """
        raise NotImplementedError('Subclasses of the AbstractConverter must implement the validate_configuration method')

    def supports(self, input_file):
        """
        simple method to check whether this converter supports the given file
        :param input_file: the file to be converted (potentially)
        :return:
        """
        return path.split(input_file)[1] in self.supported_filetypes

    def convert(self, input_file, output_folder):
        """
        converts the given input file to be compatible with the specified platform
        :param input_file:
        :param output_folder:
        :return:
        """
        raise NotImplementedError('Subclasses of the AbstractConverter must implement the convert method')


class AbstractFbxConverter(AbstractConverter):
    """
    Base Converter for fbx files
    """
    supported_filetypes = ['.fbx']


class NoopConverter(AbstractFbxConverter):
    """
    Platform independent dummy fbx converter (noop)
    """
    def convert(self, input_file, output_folder):
        """
        noop conversion process -> copy input_file(s) to output_folder
        :param input_file:
        :param output_folder:
        :return:
        """
        # clean up before starting
        # clear all files from the output_folder
        # to do so, just delete the entire folder
        if path.exists(output_folder):
            shutil.rmtree(output_folder)
        # ... and recreate it afterwards
        os.makedirs(output_folder)
        # start copying everything from the input_file's folder to the output folder
        from_dir = path.dirname(input_file)
        to_dir = output_folder
        copy_tree(from_dir, to_dir)
        # return the path to the "converted" file
        return path.join(output_folder, path.basename(input_file))

    def validate_configuration(self, config):
        return True
