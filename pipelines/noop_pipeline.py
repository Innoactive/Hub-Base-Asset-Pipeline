import os
import shutil
from distutils.dir_util import copy_tree
from os import path

from pipelines.base import AbstractFbxPipeline
from logs import logger


class NoopPipeline(AbstractFbxPipeline):
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
