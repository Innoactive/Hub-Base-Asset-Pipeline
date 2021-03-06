import sys

from .command_line import main
from .logger import logger
from .pipeline import AbstractAssetPipeline, \
    BaseRemoteAssetPipeline, \
    NoopRemoteAssetPipeline, \
    PlatformSpecificAssetPipelineMixin
from .protocol import *
from .chunked_upload import ChunkedUploadMixin

__all__ = [
    'logger',
    'AbstractAssetPipeline',
    'BaseRemoteAssetPipeline',
    'NoopRemoteAssetPipeline',
    'PlatformSpecificAssetPipelineMixin',
    'ConversionState',
    'MessageType',
    'ChunkedUploadMixin'
]

if __name__ == '__main__':
    main(sys.argv[1:])
