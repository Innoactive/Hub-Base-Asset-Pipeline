# holocloud - Asset Pipeline

This is the base repository for any asset pipeline that can work together with the holocloud.

A remote asset pipeline is a service that can run anywhere and will communicate with the holocloud
via the available APIs.

The tasks of an asset pipeline can range from simple tasks like asset conversion or optimization up
to more complex tasks like asset classification.

Remote asset pipelines can be scaled individually and independently of the holocloud.

**Any implementation of a specific asset pipeline (e.g. for pdf files or 3d models in the fbx format) 
will use this connector package and its base pipeline implementation as a pip package.**

For more information on the architecture of the holocloud ecosystem, please refer to the [holocloud's
documentation](https://github.com/Innoactive/HOLOCLOUD-backend) directly.

## How to Use

Use this pip package in a concrete implementation of an asset pipeline by installing it in the following way using pip:

```bash
pip install -U git+https://github.com/Innoactive/HOLOCLOUD-asset-pipeline-connector@0.1.0
```

Afterwards, your pipeline implementation should be based on `AbstractPipeline`. 

You can establish a connection between your newly created pipeline and the holocloud® by running
`xyz - todo` and providing configuration like // TODO.

#### Requirements

- Python 2.7.x
