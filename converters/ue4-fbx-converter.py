
#!/usr/bin/python

import os, sys, getopt, subprocess, zipfile, shutil, json
from os import path
import logging
import importlib
fbxConverter = importlib.import_module("base-fbx-converter")

class UE4FbxConverter(fbxConverter.ConfigurableFbxConverter):
    def validateConfiguration(self, config):
        root_path = config['unreal']['converter-root']
        # check if the root folder actually exists, else exit
        assert path.exists(root_path), 'Invalid Root path'
        return True

    def convert(self, input, output):
        root_path = self.config['unreal']['converter-root']
        # path to the unreal engine editor's executable
        # t.b.d. make sure ue4 is installed correctly
        editor_path = path.join(root_path, *['Engine', 'Engine', 'Binaries', 'Win64', 'UE4Editor.exe'])
        cooking_project_path = path.join(root_path, 'CookingProject')
        cooking_project_file = path.join(cooking_project_path, 'CookingProject.uproject')
        cooking_project_content_path = path.join(cooking_project_path, *['Content', 'Imported'])
        cooking_project_cooking_path = path.join(cooking_project_path, *['Saved', 'Cooked'])

        # clean up before starting
        # clear all files from the cooking project's content folder
        # to do so, just delete the entire folder
        if path.exists(cooking_project_content_path):
            shutil.rmtree(cooking_project_content_path)
            # ... and recreate it afterwards
            os.makedirs(cooking_project_content_path)
        if path.exists(cooking_project_cooking_path):
            shutil.rmtree(cooking_project_cooking_path)
            # ... and recreate it afterwards
            os.makedirs(cooking_project_cooking_path)

        # t.b.d. assert that all paths and referenced files exist correctly
        # run the fbx importer commandlet (importing fbx files and converting them to .uassets)
        fbx_import_cmd = '{0} {1} -run=ImportFbx file="{2}" dest={3}'.format(
          editor_path,
          cooking_project_file,
          input,
          cooking_project_content_path + path.sep
        )
        logging.info('Importing ... {}'.format(fbx_import_cmd))
        try:
            import_result = subprocess.check_output(fbx_import_cmd,
              stderr=subprocess.STDOUT,
              shell=False)
            # check the output and whether we got a success
            # 3rd line from end holds the result of the operation
            lines = import_result.split('\n')
            import_result_line = lines[len(lines) - 3]
        except subprocess.CalledProcessError as err:
            logging.error(err.output)
        # make sure the operation was successful
        assert 'Success' in import_result_line, 'FBX Import Command was not successful'
        # also store how long the import command took us. Might be interesting later on
        import_duration_line = lines[len(lines) - 1]
        # run the cooking commandlet (preparing .uassets for platforms - in this case: windows)
        cooking_cmd = '{0} {1} -run=cook -targetplatform=WindowsNoEditor'.format(
          editor_path,
          cooking_project_file,
        )
        logging.info('Cooking ... {}'.format(cooking_cmd))
        try:
            cooking_result = subprocess.check_output(cooking_cmd.split(' '),
              stderr=subprocess.STDOUT,
              shell=False)
            lines = cooking_result.split('\n')
            cooking_result_line = lines[len(lines) - 3]
        except subprocess.CalledProcessError as err:
            logging.error(err.output)

        # make sure the operation was successful
        assert 'Success' in cooking_result_line, 'FBX Import Command was not successful'
        # also store how long the import command took us. Might be interesting later on
        cooking_duration_line = lines[len(lines) - 1]
        # now that the contents are cooked, we are nearly done
        # we need to copy the resulting files to the output folder
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
        # loop over all files in the imported folder
        cooked_output_path = path.join(cooking_project_cooking_path, *['WindowsNoEditor', 'CookingProject', 'Content', 'Imported'])
        for file in os.listdir(cooked_output_path):
          # only copy uassets and fuck the rest
          if os.path.splitext(file)[1] == '.uasset':
            absolute_file_path = path.join(cooked_output_path, file)
            # copy the file
            shutil.copy(absolute_file_path, new_output_folder)
            # if the filename is the same as the imported fbx, then we're dealing
            # with the actual model file
            # FIXME: Unreal seems to replace dots in filenames by underscore during import
            # we should have a more beautiful way of checking this
            if filename.replace('.', '_') == os.path.splitext(file)[0]:
              imported_model_path = path.join(new_output_folder, file)
            # otherwise, it's an imported material
            else:
              imported_material_paths.append(path.join(new_output_folder, file))
        # 2. create a summary of our operation in a json format
        summary = {
          'model': imported_model_path,
          'materials': imported_material_paths
        }
        # generate a json file containing all the information
        summary_json_path = path.join(new_output_folder, 'result.json')
        f = open(summary_json_path, 'w')
        json.dump(summary, f)
        return summary

if __name__ == "__main__":
    converter = UE4FbxConverter()
    converter.main(sys.argv[1:])
