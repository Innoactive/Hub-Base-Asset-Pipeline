# coding=utf-8
import os

from setuptools import setup


def readme():
    """
    try to read the readme.md file and emit it's content as
    python-friendly ReStructuredText
    :return:
    """
    readme_name = 'readme.md'
    if os.path.isfile(readme_name):
        try:
            from pypandoc import convert
            return convert(readme_name, 'rst')
        except ImportError:
            print("warning: pypandoc module not found, could not execute Markdown to RST")
            with open(readme_name) as f:
                return f.read()

setup(name='holocloud-asset-pipeline',
      version='0.1',
      description='Tools to connect a new asset pipeline to the holocloud®',
      long_description=readme(),
      url='http://github.com/Innoactive/HOLOCLOUD-pipeline-connector',
      author='Benedikt Reiser',
      author_email='benedikt.reiser@gmail.com',
      license='MIT',
      keywords=['holocloud', 'assets', 'pipeline', 'connector', 'websocket'],
      packages=['asset_pipeline'],
      install_requires=[
          'PyYAML',
          'requests',
          'websocket-client'
      ],
      entry_points={
          'console_scripts': ['start-asset-pipeline=asset_pipeline.command_line:main'],
      },
      include_package_data=True,
      zip_safe=False)