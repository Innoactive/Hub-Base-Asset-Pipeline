
#!/usr/bin/python

import os, sys, getopt, subprocess, zipfile, shutil, json, re
from os import path, listdir
import logging
import importlib
fbxConverter = importlib.import_module("unity-fbx-converter")
from distutils.dir_util import copy_tree

class DummyFbxConverter(fbxConverter.UnityFbxConverter):

    def validateConfiguration(self, config):
        return True

    def convert(self, input, output):
        # fuck them materials
        imported_material_paths = []
        # list files in input folder
        from os import listdir
        onlyfiles = [f for f in listdir(input) if path.isfile(path.join(input, f))]
        logging.info(onlyfiles)
        # take the first file
        if len(onlyfiles) > 0:
            imported_model_path = path.splitext(path.basename(onlyfiles[0]))[0]  + '.unity3d'
            # copy the first file to the output folder
            shutil.copy(path.join(input, onlyfiles[0]), path.join(output, imported_model_path))
        else:
            raise Error('No files found')
        # 2. create a summary of our operation in a json format
        summary = {
          'model': imported_model_path,
          'materials': imported_material_paths
        }
        # generate a json file containing all the information
        summary_json_path = path.join(output, 'result.json')
        f = open(summary_json_path, 'w')
        json.dump(summary, f)
        return summary

if __name__ == "__main__":
    converter = DummyFbxConverter()
    converter.main(sys.argv[1:])
