# coding=utf-8
import os

from setuptools import setup, find_packages


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


setup(name='hub-asset-pipeline',
      version='1.1.1',
      description='Tools to connect a new asset pipeline to the Innoactive® Hub',
      long_description=readme(),
      url='https://github.com/Innoactive/Hub-Base-Asset-Pipeline',
      author='Benedikt Reiser',
      author_email='benedikt.reiser@gmail.com',
      license='MIT',
      keywords=['innoactive', 'hub', 'assets', 'pipeline', 'connector', 'websocket'],
      packages=find_packages(exclude=['docs', 'tests', 'tests.*']),
      install_requires=[
          'requests_oauthlib==0.8.0',
          'websocket-client==0.44.0',
          'oauthlib-extras'
      ],
      entry_points={
          'console_scripts': ['start-asset-pipeline=asset_pipeline.command_line:main'],
      },
      test_suite='nose.collector',
      tests_require=['nose', 'requests-mock'],
      include_package_data=True,
      zip_safe=False)
