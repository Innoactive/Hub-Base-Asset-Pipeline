# Innoactive Hub - Asset Pipeline

This is the base repository for any asset pipeline that can work together with the holocloud.

A remote asset pipeline is a service that can run anywhere and will communicate with the holocloud
via the available APIs.

The tasks of an asset pipeline can range from simple tasks like asset conversion or optimization up
to more complex tasks like asset classification.

Remote asset pipelines can be scaled individually and independently of the holocloud.

**Any implementation of a specific asset pipeline will use this connector package and its base pipeline implementation 
as a pip package.**

For more information on the architecture of the Innoactive Hub ecosystem, please refer to the [
documentation](https://github.com/Innoactive/Hub-Backend) directly.

## How to Use

Use this pip package in a concrete implementation of an asset pipeline by installing it in the following way using pip:

```bash
pip install -U git+https://github.com/Innoactive/Hub-Base-Asset-Pipeline.git@0.1.0
```

Afterwards, your pipeline implementation should be based on `BaseRemoteAssetPipeline`. 

You can establish a connection between your newly created pipeline and the Innoactive Hub® by creating 
a command line script like the following: 

```python
import asset_pipeline.arguments as arguments
from <your-pipeline-module> import <YourAssetPipelineImplementation>

def main():
    # parse all available configuration information
    config = arguments.parse()
    print config
    # create new RemoteAssetPipeline instance and connect to the Hub
    asset_pipeline = <YourAssetPipelineImplementation>(
        config=config
    )
    asset_pipeline.start()

if __name__ == "__main__":
    main()

```

and running it via `python command_line.py`, optionally providing a configuration file `pipeline.ini` 
like the following. All of these settings will be forwarded to your pipeline implementation if you call
`python command_line.py -c pipeline.ini`.

```ini
[Connection]
host=127.0.0.1
port=8000
[Pipeline]
my_custom_setting=123
foo=bar
```

## Requirements

- Python 2.7.x

## Existing Pipelines

The following pipelines have already been successfully implemented and integrated with the Innoactive Hub®:

- [PDF Conversion Pipeline](https://github.com/Innoactive/Hub-PDF-Pipeline)
  
  Reads in a pdf file and outputs a set of high-resolution images that can be easily rendered
