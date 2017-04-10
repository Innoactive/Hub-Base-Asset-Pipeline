import arguments
from pipeline import NoopRemoteAssetPipeline


def main():
    # parse all available configuration information
    config = arguments.parse()
    # create new RemoteAssetPipeline instance
    # and connect to socket.io server
    asset_pipeline = NoopRemoteAssetPipeline(
        config=config
    )
    asset_pipeline.start()


if __name__ == "__main__":
    main()
