
class MissingHeaderCheckScriptError(RuntimeError):
    """
    Error indicating problems with missing header in check script.
    """
    def __init__(self, script=""):
        if script:
            message = "A header missing in the %s check script" % script
        else:
            message = "A header missing in a check script"
        RuntimeError.__init__(self, "Error: " + message)


class ModuleSetFormatError(RuntimeError):
    """
    Module set has wrong format

    A mandatory part is missing, has wrong mode, etc.
    """
    def __init__(self, reason, subject="", e=None):
        lines = ["Module set has wrong format:"]
        lines.append("    reason: %s" % reason)
        if subject:
            lines.append("    subject: %s" % subject)
        if e is not None:
            lines.append("    error: %s" % e)
        RuntimeError.__init__(self, "Error: " + '\n'.join(lines))


class ModuleSetInitError(RuntimeError):
    """
    Module set init script failed
    """
    def __init__(self, returncode, stderr=""):
        lines = ["Module set init script reported error:"]
        if returncode:
            lines.append("    status: %s" % returncode)
        if stderr:
            for line in stderr.strip('\n').split('\n'):
                lines.append("    stderr: %s" % line)
        RuntimeError.__init__(self, "Error: " + '\n'.join(lines))


class MissingFileInContentError(RuntimeError):
    """
    Some file is missing in a module.
    """
    def __init__(self, file="", dir=""):
        if file and dir:
            message = "File %s missing in the module directory %s" \
                      % (file, dir)
        else:
            message = "File(s) missing in a module"
        RuntimeError.__init__(self, "Error: " + message)


class MissingTagsIniFileError(RuntimeError):
    """
    Some tags are missing in INI file.
    """
    def __init__(self, tags="", ini_file=""):
        if tags and ini_file:
            message = "Tag(s) %s missing in the %s file" % (tags, ini_file)
        else:
            message = "Tag(s) missing in an INI file"
        RuntimeError.__init__(self, "Error: " + message)


class EmptyTagGroupXMLError(ValueError):
    """
    One of the tags in group.xml (to be merged into all-xccdf.xml for
    OpenSCAP) is empty.
    """
    def __init__(self, tag=""):
        if tag:
            message = "Tag %s in a group.xml can't be empty" % tag
        else:
            message = "A tag in a group.xml can't be empty"
        ValueError.__init__(self, "Error: " + message)
