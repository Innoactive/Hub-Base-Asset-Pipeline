
#!/usr/bin/python

import os, sys, getopt, subprocess, zipfile, shutil, json, re
from os import path
import logging
import importlib
fbxConverter = importlib.import_module("base-fbx-converter")
from distutils.dir_util import copy_tree

class UnityFbxConverter(fbxConverter.ConfigurableFbxConverter):
    USAGE_MESSAGE = 'usage: {} -i <inputFolder> -o <outputFolder>'.format(__file__)

    def validateArgs(self, argv):
        inputFolder = ''
        outputFolder = ''
        try:
            opts, args = getopt.getopt(argv,"hi:o:",["ifolder=","ofolder="])
        except getopt.GetoptError:
            print_usage()
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print_usage()
                sys.exit()
            elif opt in ("-i", "--ifolder"):
                inputFolder = arg
            elif opt in ("-o", "--ofolder"):
                outputFolder = arg

        # assert we got input file and output folder arguments
        assert inputFolder, 'Please pass an input folder to the script. {}'.format(self.USAGE_MESSAGE)
        assert outputFolder, 'Please pass an output folder to the script. {}'.format(self.USAGE_MESSAGE)

        # check that the input file actually exists, else exit
        assert path.exists(inputFolder), 'Please pass a valid input folder to the script'
        # input needs to be a dir
        assert path.isdir(inputFolder), 'Input path must be a directory'
        # check that the output file actually exists, else exit
        # assert path.exists(outputFolder), 'Please pass a valid output folder to the script'

        print 'Input folder is "{}"'.format(inputFolder)
        print 'Output folder is "{}"'.format(outputFolder)

        return inputFolder, outputFolder

    def validateConfiguration(self, config):
        root_path = config['unity']['converter-root']
        # check if the root folder actually exists, else exit
        assert path.exists(root_path), 'Invalid Root path'
        return True

    def getUnityEditorPath(self):
        # default installation locations based on platform
        default64 = r'C:\Program Files\Unity\HTP\Editor\Unity.exe'
        default32 = r'C:\Program Files (x86)\Unity\Editor\Unity.exe'
        defaultConfig = self.config.get('unity').get('editor-path', 'unavailable')
        # try default locations
        pth = ''
        if path.exists(defaultConfig):
            pth = defaultConfig
        elif path.exists(default64):
            pth = default64
        elif path.exists(default32):
            pth = default32
        else:
            raise Exception('No Unity Editor executable found')
        return pth

    def convert(self, input, output):
        root_path = self.config['unity']['converter-root']
        # path to the unreal engine editor's executable
        # t.b.d. make sure ue4 is installed correctly
        editor_path = self.getUnityEditorPath()
        converter_project_path = root_path
        log_file_path = path.join(path.dirname(__file__), 'unity-fbx-converter.log')
        bundle_assets_path = path.join(converter_project_path, *['Assets', 'BundleAssets'])
        asset_bundles_path = path.join(converter_project_path, *['Assets', 'AssetBundles'])

        # clean up before starting
        # clear all files from the converters project's content folder
        # to do so, just delete the entire folder
        if path.exists(bundle_assets_path):
            shutil.rmtree(bundle_assets_path)
        # ... and recreate it afterwards
        os.makedirs(bundle_assets_path)
        if path.exists(asset_bundles_path):
            shutil.rmtree(asset_bundles_path)
        # ... and recreate it afterwards
        os.makedirs(asset_bundles_path)

        # some assertions
        assert path.exists(bundle_assets_path), 'Bundle Assets path does not exist'
        assert path.exists(asset_bundles_path), 'Asset Bundle path does not exist'

        # next up, copy all files from the input folder to the converter project's bundle assets folder
        # that way, unity knows about the files (fbx, materials, w/e) and can convert them to an asset_bundles_path
        # copy subdirectory example
        fromDirectory = input
        toDirectory = bundle_assets_path
        copy_tree(fromDirectory, toDirectory)

        # t.b.d. assert that all paths and referenced files exist correctly
        # run the fbx importer commandlet (importing fbx files and converting them to .uassets)
        fbx_import_cmd = '{0} -quit -nographics -batchmode -force-free -projectPath {1} -executeMethod AutoAssetBundles.AutoBuild -logFile "{2}"'.format(
          editor_path,
          converter_project_path,
          log_file_path
        )
        logging.info('Importing ... {}'.format(fbx_import_cmd))
        try:
            import_result = subprocess.check_output(fbx_import_cmd,
              stderr=subprocess.STDOUT,
              shell=False)
            # if we get here, we are successful
            # also store how long the import command took us. Might be interesting later on
            # to do so, take a look at the log file that has been written
            logfile = open(log_file_path, 'r')
            # compile our regular expression to find the result line in the logfile
            regex = re.compile('^----- Total AssetImport time:\s([0-9\.]*s)(.*)\[([0-9\.]*)\s.*\s([0-9\.]*)\smb/s\]')
            import_duration = '0s'
            for line in logfile:
                match = regex.search(line)
                if match and float(match.group(3)) > 0 :
                    import_duration = match.group(1)
            print 'Import took {}'.format(import_duration)
            # now that the contents are converted to an asset bundle, we are nearly done
            # we need to copy the resulting asset bundle to the output folder
            # and create a summary of the operations that we did
            # initialize some variables to store results
            imported_model_path = None
            imported_material_paths = []
            # also we need to clean up the mess we created in the cooking project's folders
            # 1. copy the results to the desired output folder
            filename = path.splitext(path.basename(input))[0]
            # create a new folder with the name of the fbx file
            new_output_folder = output
            if not os.path.exists(new_output_folder):
              os.makedirs(new_output_folder)
            # search for the virtual-showroom-bundle in the asset_bundles_path output path
            asset_bundle_path = path.join(asset_bundles_path, 'virtual-showroom-bundle')
            if path.exists(asset_bundle_path):
                shutil.copy(asset_bundle_path, path.join(new_output_folder, path.basename(input))  + '.unity3d')
                imported_model_path = path.join(new_output_folder, path.basename(input)) + '.unity3d'
            else:
                raise Error('No Asset Bundle found')
            # 2. create a summary of our operation in a json format
            summary = {
              'model': imported_model_path,
              'materials': imported_material_paths,
              'success': True
            }
            # generate a json file containing all the information
            summary_json_path = path.join(new_output_folder, 'result.json')
            f = open(summary_json_path, 'w')
            json.dump(summary, f)
        except subprocess.CalledProcessError as err:
            logging.error('Got error in command "{0}". Command exited with code {1} and output {2}'.format(err.cmd, err.returncode, err.output))
            summary = {
                'success': False,
                'error': err.output
            }
        return summary

if __name__ == "__main__":
    converter = UnityFbxConverter()
    converter.main(sys.argv[1:])
