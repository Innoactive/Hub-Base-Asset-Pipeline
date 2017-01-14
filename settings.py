# construct the path to the output folder
# make this system independent by using lots of
# python's os functions
from os import path

# folder in which we'll download temporary files
TMP_FILES_PATH = path.abspath(
    path.join(
        path.dirname(path.realpath(__file__)),
        'tmp'
    )
)

# the header to be used to identify the platform of a converter
PLATFORM_SLUG_HEADER = "Holocloud-Converter-Slug"


class MessageType(object):
    """
    list of available message types
    will be included in any json message as "type": "Message Type" on top level
    """
    CONVERSION_START = 'CONVERSION_START'
    CONVERSION_PROGRESS = 'CONVERSION_PROGRESS'
    CONVERSION_SUCCESS = 'CONVERSION_SUCCESS'
    CONVERSION_FAIL = 'CONVERSION_FAIL'


class ConversionState(object):
    """
    list of available conversion states for 3d assets
    """
    PENDING = u'pen'
    IN_PROGRESS = u'pro'
    FINISHED = u'fin'
    ERROR = u'err'
    WARNING = u'war'
