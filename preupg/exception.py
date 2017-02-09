
class MissingHeaderCheckScriptError(RuntimeError):
    """
    Error indicating problems with missing header in check script
    """
    def __init__(self, script=""):
        if script:
            message = "A header missing in the {0} check script".format(script)
        message = "A header missing in a check script"
        super(MissingHeaderCheckScriptError, self).__init__(message)


class MissingFileInContentError(RuntimeError):
    """
    Some file is missing in a module
    """
    def __init__(self, module=""):
        if module:
            message = "File(s) missing in the {0} module".format(module)
        message = "File(s) missing in a module"
        super(MissingFileInContentError, self).__init__(message)


class MissingTagsIniFileError(RuntimeError):
    """
    Some tags are missing in INI file
    """
    def __init__(self, tags="", ini_file=""):
        if tags and ini_file:
            message = "Tag(s) {0} missing in the {1} file".format(ini_file)
        message = "Tag(s) missing in an INI file"
        super(MissingTagsIniFileError, self).__init__(message)


class EmptyTagIniFileError(RuntimeError):
    """
    Some tag is empty. It is not approved
    """
    def __init__(self, tag="", ini_file=""):
        if tag and ini_file:
            message = "Tag {0} in the {1} file can't be replaced with an" \
                      " empty string".format(tag, ini_file)
        message = "Replacing a tag in an INI file with an empty string - not" \
                  " allowed"
        super(EmptyTagIniFileError, self).__init__(message)
