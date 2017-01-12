import posixpath
from os import path


def convert_posix_path_to_os_path(pth):
    """
    converts the given posix path (a/b/c) into an os specific path (e.g. Windows: a\b\c)

    :param pth: the path in posix format
    :return: the path in os specific format
    """
    # split the path into its components
    folders = []
    while 1:
        pth, folder = path.split(pth)

        if folder != "":
            folders.append(folder)
        else:
            if pth != "":
                folders.append(pth)
            break
    folders.reverse()
    return path.join(*folders)


def convert_os_path_to_posix_path(pth):
    """
    converts the given os specific path (e.g. Windows: a\b\c) into a posix path (a/b/c)

    :param pth: the path in os specific format
    :return: the path in posix format
    """
    # split the path into its components
    folders = []
    while 1:
        pth, folder = path.split(pth)

        if folder != "":
            folders.append(folder)
        else:
            if pth != "":
                folders.append(pth)
            break

    folders.reverse()
    return posixpath.join(*folders)
