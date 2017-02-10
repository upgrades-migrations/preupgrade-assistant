class DummyConfKickstart(object):
    """
    Dummy conf class for Conf

    use it like this:
    conf = Conf(DummyConf(id=123, skip_common=True))
    """
    def __init__(self, **kwargs):
        self.settings = kwargs

    def __getattr__(self, name):
        try:
            return self.settings.get(name)
        except AttributeError:
            return object.__getattribute__(self, name)


class ConfKickstart(object):
    """
    configuration of preupgrade assistant

    merged values from CLI and settings.py
    """

    def __init__(self, *args):
        """
        *args - list of objects with settings attached as
                attributes to these objects
        priority:
            args[0] > args[1] > ...
        """
        self.settings = list(args)

    def insert(self, pos, settings):
        self.settings.insert(pos, settings)

    def __getattr__(self, name):
        for arg in self.settings:
            try:
                value = getattr(arg, name)
            except AttributeError:
                continue
            if value is not None and value != "":
                return value
            else:
                continue
        return None
