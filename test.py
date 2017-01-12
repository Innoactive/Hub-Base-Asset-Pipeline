import time

import thread
import websocket
import logging
import json

# our logging instance
logger = logging.getLogger('unity-converter')
logger.setLevel(logging.INFO)
logging.warning('Watch out!')


def on_message(ws, msg):
    #print msg
    logger.info('message: %s' % msg)
    pass


def on_error(ws, error):
    logger.info(error)


def on_close(ws):
    logger.info("### closed ###")


def on_open(ws):
    logger.info("### connected ###")
    ws.send("\"Hello %d\"" % 1)
    ws.send(json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}]))


if __name__ == "__main__":
    #websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:8000/assets/pipeline/",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
