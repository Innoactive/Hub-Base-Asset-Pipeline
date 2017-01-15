from os import path


class AbstractPipeline(object):
    """
    base converter implementation from which all pipelines are to be derived
    """
    # list of filetypes this converter can handle
    supported_filetypes = []

    # configuration options
    config = None

    def __init__(self, config=None):
        if config is not None:
            # validate the configuration
            if self.validate_configuration(config):
                self.config = config
            else:
                raise AttributeError('The provided configuration could not be validated. Please verify!')

    def validate_configuration(self, config):
        """
        validates the given configuration with respect to the converter instance
        :param config:
        :return:
        """
        raise NotImplementedError('Subclasses of the AbstractPipeline must implement the validate_configuration method')

    def supports(self, input_file):
        """
        simple method to check whether this converter supports the given file
        :param input_file: the file to be converted (potentially)
        :return:
        """
        return path.split(input_file)[1] in self.supported_filetypes

    def convert(self, input_file, output_folder):
        """
        converts the given input file to be compatible with the specified platform
        :param input_file:
        :param output_folder:
        :return:
        """
        raise NotImplementedError('Subclasses of the AbstractPipeline must implement the convert method')

    def __str__(self):
        return '%s' % self.__class__.__name__


class AbstractFbxPipeline(AbstractPipeline):
    """
    Base RemoteAssetPipeline for fbx files
    """
    supported_filetypes = ['.fbx']


class AbstractZippedFbxPipeline(AbstractFbxPipeline):
    """
    Base RemoteAssetPipeline for fbx files
    """
    supported_filetypes = ['.zip']
