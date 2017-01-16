import subprocess
import zipfile
import os
import shutil
from distutils.dir_util import copy_tree
from os import path
from _winreg import *

import re

from logs import logger
from pipelines.base import AbstractZippedFbxPipeline


class UnityZippedFbxPipeline(AbstractZippedFbxPipeline):
    unity_executable = None
    unity_converter_project_path = None

    def convert(self, input_file, output_folder):
        """
        conversion takes place in several steps
        1. unzip the zip archive
        2. copy all files to the unity conversion project
        3. run the unity conversion command
        4. copy back the converted results (Unity AssetBundle) to the output folder
        :param input_file: path to the input file (zip)
        :param output_folder: path to the folder in which to copy the resulting file
        :return:
        """
        # step 1, unzip files
        unzip_folder = path.splitext(input_file)[0]
        if not path.exists(unzip_folder):
            os.makedirs(unzip_folder)
        self.unzip(input_file, unzip_folder)
        # step 2, copy files to unity converter project
        # path to which assets to be bundled are to be copied
        bundle_assets_path = path.join(self.unity_converter_project_path, *['Assets', 'BundleAssets'])
        # path from which we'll retrieve the AssetBundle (= conversion result)
        asset_bundles_path = path.join(self.unity_converter_project_path, *['Assets', 'AssetBundles'])
        # clean up before starting
        # clear all files from the pipelines project's content folder
        # to do so, just delete the entire folder
        if path.exists(bundle_assets_path):
            shutil.rmtree(bundle_assets_path)
        # ... and recreate it afterwards
        os.makedirs(bundle_assets_path)
        if path.exists(asset_bundles_path):
            shutil.rmtree(asset_bundles_path)
        # ... and recreate it afterwards
        os.makedirs(asset_bundles_path)
        # next up, copy all files from the input folder to the converter project's bundle assets folder
        # that way, unity knows about the files (fbx, materials, w/e) and can convert them to an AssetBundle
        from_folder = unzip_folder
        to_folder = bundle_assets_path
        copy_tree(from_folder, to_folder)
        # step 3, run the unity conversion command
        log_file_path = path.abspath(path.join(path.dirname(input_file), '..', 'unity-fbx-converter.log'))
        # run the fbx importer commandlet (importing fbx files and converting them to an Assetbundle)
        fbx_import_cmd = '{0} -quit -nographics -batchmode -force-free ' \
                         '-projectPath {1} ' \
                         '-executeMethod AutoAssetBundles.AutoBuild ' \
                         '-logFile "{2}"'.format(self.unity_executable, self.unity_converter_project_path,
                                                 log_file_path)
        logger.info('Importing ... {}'.format(fbx_import_cmd))
        try:
            import_result = subprocess.check_output(fbx_import_cmd,
                                                    stderr=subprocess.STDOUT,
                                                    shell=False)
            # if we get here, we are successful (probably)
            # let's check ...
            regex_fail = re.compile('\*\*\*\s*Cancelled \'Build\.AssetBundle.*')
            # also store how long the import command took us. Might be interesting later on
            # compile our regular expression to find the result line in the logfile
            import_duration = '0s'
            regex_duration = re.compile(
                '^----- Total AssetImport time:\s([0-9\.]*s)(.*)\[([0-9\.]*)\s.*\s([0-9\.]*)\smb/s\]')
            # to do so, take a look at the log file that has been written
            logfile = open(log_file_path, 'r')
            for line in logfile:
                match_fail = regex_fail.search(line)
                if match_fail:
                    logger.error(
                        'Conversion process failed. Please take a look at the logs located at %s for details' % log_file_path)
                    return None
                match_duration = regex_duration.search(line)
                if match_duration and float(match_duration.group(3)) > 0:
                    import_duration = match_duration.group(1)
            logger.info('Import took {}'.format(import_duration))
            # now that the contents are converted to an asset bundle, we are nearly done
            # step 4, check results and copy back converted results
            # search for the virtual-showroom-bundle in the asset_bundles_path output path
            conversion_result_path = path.join(asset_bundles_path, 'virtual-showroom-bundle')
            if path.exists(conversion_result_path):
                conversion_result_path_final = path.join(output_folder, path.basename(input_file)) + '.unity3d'
                shutil.copy(conversion_result_path, path.join(output_folder, path.basename(input_file)) + '.unity3d')
                return conversion_result_path_final
            else:
                logger.error('No Asset Bundle found. Apparently the conversion didn\'t go through as expected.'
                             'You might wanna take a look at the log file at %s' % log_file_path)
                return None
        except subprocess.CalledProcessError as err:
            logger.error('Got error in command "{0}". '
                         'Command exited with code {1} and output {2}'.format(err.cmd,
                                                                              err.returncode,
                                                                              err.output))
            return None

    def validate_configuration(self, config):
        """
        validates the given configuration with respect to all the required options

        Required options for the Unity converter are:
        - unity_executable: Path to unity executable
        - unity_converter_project_path: Path to unity conversion project

        :param config:
        :return:
        """
        # find the unity executable
        self.unity_executable = self.find_unity_executable(config)
        if self.unity_executable is None:
            logger.error(
                'Could not locate Unity executable. Please install Unity or if you have already, '
                'make sure to specify the path correctly in the config.yml')
            return False
        # locate the unity project path
        self.unity_converter_project_path = self.find_unity_converter_project(config)
        if self.unity_converter_project_path is None:
            logger.error(
                'Could not locate the Unity converter project. '
                'Please make sure to specify the path to the converter project via the config.yml. ')
            return False
        # if we got here, everything's fine
        return True

    def find_unity_executable(self, config):
        """
        attempts to find the path to the Unity.exe by trying several options like the config specified path or Windows
        registry
        :param config:
        :return:
        """
        # check if the path to unity has been provided in the config
        if 'unity_executable' in config:
            # if a path has been provided, make sure it exists and points to an actual file
            unity_executable = config.get('unity_executable')
            if path.isfile(unity_executable):
                logger.info('Found Unity executable as specified in the config at "%s"' % unity_executable)
                return unity_executable
            logger.info(
                'Couldn\'t find Unity executable at the specified path "%s". '
                'Checking Windows registry ...' % unity_executable)
        # otherwise, try checking the registry
        unity_executable = self.find_unity_in_win_registry()
        if path.isfile(unity_executable):
            logger.info('Found Unity executable as via querying the Windows registry at "%s"' % unity_executable)
            return unity_executable
        logger.info('Couldn\'t find Unity at neither the specified path nor via the Windows registry.')
        return None

    @staticmethod
    def unzip(source_filename, dest_dir):
        with zipfile.ZipFile(source_filename) as zf:
            for member in zf.infolist():
                # Path traversal defense copied from
                # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
                words = member.filename.split('/')
                pth = dest_dir
                for word in words[:-1]:
                    while True:
                        drive, word = path.splitdrive(word)
                        head, word = path.split(word)
                        if not drive:
                            break
                    if word in (os.curdir, os.pardir, ''):
                        continue
                    pth = path.join(pth, word)
                zf.extract(member, pth)

    @staticmethod
    def find_unity_in_win_registry():
        """
        opens up the windows registry in the hopes of finding the path to the unity executable

        However, one drawback is that the registry only points to the last version of Unity that
        has been installed. E.g. if you first install version 5.5 and 5.4 afterwards,
        the registry will point to 5.4.
        (see HKEY_CURRENT_USER\SOFTWARE\Unity Technologies\Installer\Unity)

        :return: the path to the unity executable if it has been found, false otherwise
        """
        # name of the unity installer dir
        key_name = r"SOFTWARE\Unity Technologies\Installer\Unity"
        logger.debug('Trying to find out Unity executable path from %s\\%s' % (HKEY_CURRENT_USER, key_name))
        # try to connect to the windows registry
        try:
            open_registry = ConnectRegistry(None, HKEY_CURRENT_USER)
            # try going into the unity installer directory of registry keys
            try:
                open_key = OpenKey(open_registry, key_name)
                logger.debug('Successfully opened %s\\%s' % (HKEY_CURRENT_USER, key_name))
                # look for two values specifically
                # installation path
                pth, regtype = QueryValueEx(open_key, 'Location x64')
                # and version
                version, regtype = QueryValueEx(open_key, 'Version')
                logger.info('Found Unity %s at %s' % (version, pth))
                # close the file handle again
                CloseKey(open_key)
                # return the path
                return path.join(pth, 'Editor', 'Unity.exe')
            except WindowsError as e:
                logger.error('Could not access key %s\\%s' % (HKEY_CURRENT_USER, key_name))
                logger.error(str(e))
            # in any case, clean up and close the registry handle
            CloseKey(open_registry)
        except WindowsError:
            logger.error('Could not open registry at %s' % HKEY_CURRENT_USER)
        return None

    @staticmethod
    def find_unity_converter_project(config):
        """
        attempts to locate the unity converter project which we need in order to convert 3d assets to Unity AssetBundles

        :param config:
        :return:
        """
        # check if the path to the converter project has been provided in the config
        if 'unity_converter_project_path' in config:
            # if a path has been provided, make sure it exists and points to an actual file
            unity_converter_project_path = config.get('unity_converter_project_path')
            if path.isdir(unity_converter_project_path):
                logger.info(
                    'Found Unity converter project as specified in the config at "%s"' % unity_converter_project_path)
                return unity_converter_project_path
            logger.info(
                'Couldn\'t find Unity converter project path at the specified path "%s". '
                'Checking default location instead ...' % unity_converter_project_path)
        # otherwise, try checking the default location
        default_unity_converter_project_path = path.abspath(
            path.join(path.dirname(os.path.realpath(__file__)), '..', 'unity-converter-project'))
        logger.info(default_unity_converter_project_path)
        if path.isdir(default_unity_converter_project_path):
            logger.info(
                'Found Unity converter project at the default location at "%s"' % default_unity_converter_project_path)
            return default_unity_converter_project_path
        logger.info('Couldn\'t find the Unity converter project at neither the specified path nor the default path.')
        return None  # class UnityFbxConverter(fbxConverter.ConfigurableFbxConverter):
