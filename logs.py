import logging

# logging configuration
logging.basicConfig(level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARN)
logging.getLogger('websocket-client').setLevel(logging.INFO)
# export a reference to our logger
logger = logging.getLogger('holocloud-converter')
