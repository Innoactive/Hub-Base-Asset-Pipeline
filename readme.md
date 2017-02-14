# holocloud - Remote Asset Pipeline

This is the base repository for any remote asset pipeline that can work together with the holocloud.

A remote asset pipeline is a service that can run anywhere and will communicate with the holocloud
via the available APIs.

The tasks of an asset pipeline can range from simple tasks like asset conversion or optimization up
to more complex tasks like asset classification.

Remote asset pipelines can be scaled individually and independently of the holocloud.

For more information on the architecture of the holocloud ecosystem, please refer to the [holocloud's
documentation](https://github.com/Innoactive/HOLOCLOUD-backend) directly.

## How to Use

t.b.d

## Requirements

- Python 2.7.x
- Virtualenv

## Setup

### Submodules

Before installing anything, make sure that you have correctly set up your git repository and initialized
all git submodules. To do so, run

```
git submodule update --init --recursive
```

### Dependencies

Run `virtualenv venv` in the project's folder. Afterwards activate the virtual environment by running
`.\venv\Scripts\activate` (or similar, depending on your terminal). Last but not least, install
all requirements in the virtual environment by running `pip install -r requirements.txt`.

You should now be good to go and start the pipeline with `python pipeline.py`. However, check
out the [configuration](#configuration) part for more information on the available options.

## Configuration

The holocloud asset pipeline can be configured through the provided `config.yml` file.

Depending on the chosen pipeline implementation, different settings apply.
Please refer to the documentation of the respective pipeline for more information.

## Development

t.b.d
