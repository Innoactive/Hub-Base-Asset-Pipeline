import logging

# logging configuration
FORMAT = '[%(asctime)s - %(module)s - %(levelname)s] %(message)s'
DATE_FORMAT = '%y/%m/%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)
logging.getLogger('requests').setLevel(logging.WARN)
logging.getLogger('websocket-client').setLevel(logging.INFO)
# export a reference to our logger
logger = logging.getLogger('holocloud-converter')
logger.setLevel(logging.DEBUG)
