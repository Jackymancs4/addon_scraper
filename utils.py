def dprint(data, debug = False):
    if debug:
        print(data)
    else:
        pass


def get_temp_path(extension_name):
    temp_folder = "tmp/" + extension_name
    return temp_folder


def get_git_path(extension_name):
    git_folder = "repos/" + extension_name
    return git_folder
