# construct the path to the output folder
# make this system independent by using lots of
# python's os functions
from os import path

CONVERTED_FILES_PATH = path.abspath(
    path.join(
         '..', 'backend', 'files', 'converted'
    )
)

# construct the path to the converter script
# make this path absolute and use lots of
# python's os functions again to do so
CONVERTER_DUMMY_SCRIPT_PATH = path.normpath(
    path.join(
        path.dirname(path.realpath(__file__)),
        'external',
        'dummy_fbx_converter.py'
    )
)


# construct the path to the converter script
# make this path absolute and use lots of
# python's os functions again to do so
CONVERTER_UNREAL_SCRIPT_PATH = path.normpath(
     path.join(
        path.dirname(path.realpath(__file__)),
        'external',
        'ue4-fbx-converter.py'
    )
)


# construct the path to the converter script
# make this path absolute and use lots of
# python's os functions again to do so
CONVERTER_UNITY_SCRIPT_PATH = path.normpath(
     path.join(
        path.dirname(path.realpath(__file__)),
        'external',
        'unity_fbx_converter.py'
    )
)

# folder in which we'll download temporary files
TMP_FILES_PATH = path.abspath(
    path.join(
        path.dirname(path.realpath(__file__)),
        'tmp'
    )
)
