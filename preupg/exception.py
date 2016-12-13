
class MissingHeaderCheckScriptError(RuntimeError):
    """
    Error indicating problems with missing header in check script
    """

    pass


class MissingFileInContentError(RuntimeError):
    """
    Some file is missing in content
    """

    pass


class MissingTagsIniFileError(RuntimeError):
    """
    Some tags are missing in INI file
    """

    pass


class EmptyTagIniFileError(RuntimeError):
    """
    Some tag is empty. It is not approved
    """

    pass


class MissingElementException(Exception):
    """
    Element in xml file does not exist
    """
    pass


class EmptyTextException(Exception):
    """
    Text inside element in empty
    """
    pass


class AttrNotFoundException(Exception):
    """
    Searched attribute does not exist
    """
    pass
