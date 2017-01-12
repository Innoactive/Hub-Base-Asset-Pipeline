#!/usr/bin/python

import sys, getopt, time, os, json, logging
from os import path
logging.basicConfig(level=logging.DEBUG)

class BaseFbxConverter:
    USAGE_MESSAGE = 'usage: {} -i <inputFile> -o <outputFolder>'.format(__file__)

    def print_usage(self):
        print self.USAGE_MESSAGE

    def validateArgs(self, argv):
        inputFile = ''
        outputFolder = ''
        try:
            opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofolder="])
        except getopt.GetoptError:
            print_usage()
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print_usage()
                sys.exit()
            elif opt in ("-i", "--ifile"):
                inputFile = arg
            elif opt in ("-o", "--ofolder"):
                outputFolder = arg

        # assert we got input file and output folder arguments
        assert inputFile, 'Please pass an input file to the script. {}'.format(self.USAGE_MESSAGE)
        assert outputFolder, 'Please pass an output folder to the script. {}'.format(self.USAGE_MESSAGE)

        # check that the input file actually exists, else exit
        assert path.exists(inputFile), 'Please pass a valid input file to the script'
        # check that the output file actually exists, else exit
        # assert path.exists(outputFolder), 'Please pass a valid output folder to the script'

        print 'Input file is "{}"'.format(inputFile)
        print 'Output folder is "{}"'.format(outputFolder)

        return inputFile, outputFolder

    def convert(self, input, output):
        time.sleep(2)
        # we're done, the result of the operation is
        result = {
            'model': 'my-model.uasset',
            'materials': [
                'material-1.uasset',
                'material-2.uasset'
            ]
        }
        # create the fbx_output_folder in the output folder
        actual_output_folder = output
        if not path.exists(actual_output_folder):
            os.makedirs(actual_output_folder)
        # copy the resulting uassets to that folder
        # model file
        model_file_path = path.join(actual_output_folder, result['model'])
        f = open(model_file_path, 'w')
        # update path
        result['model'] = model_file_path
        f.write(result['model'])
        f.close()
        # materials
        for idx, material in enumerate(result['materials']):
            material_file_path = path.join(actual_output_folder, material)
            f = open(material_file_path, 'w')
            # update path
            result['materials'][idx] = material_file_path
            f.write(result['materials'][idx])
            f.close()
        # generate a json file containing all the information
        result_json_path = path.join(actual_output_folder, 'result.json')
        f = open(result_json_path, 'w')
        json.dump(result, f)
        f.close()
        print 'Copying results to "{}"'.format(actual_output_folder)
        time.sleep(1)

    def main(self, argv):
        # validte the input arguments and get the inputFile and outputFolder
        inputFile, outputFolder = self.validateArgs(argv)
        # start the conversion (this method can be overwritten in subclasses)
        result = self.convert(inputFile, outputFolder)
        # print the result json file so it can be directly processed by the converter
        print json.dumps(result)

class ConfigurableFbxConverter(BaseFbxConverter):
    def __init__(self):
        # the path to the folder in which this script resides
        # read the root path from the config.yml
        config_file = open(path.join(path.dirname(__file__), '..', 'config.yml'))
        config = json.load(config_file)
        # validate the configuration
        self.validateConfiguration(config)
        self.config = config

    def validateConfiguration(self, config):
        return True

if __name__ == "__main__":
    converter = BaseFbxConverter()
    converter.main(sys.argv[1:])
