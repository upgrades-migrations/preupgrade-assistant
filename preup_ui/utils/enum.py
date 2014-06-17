# -*- coding: utf-8 -*-

class Enum(object):
    """Enumerated objects."""
    __slots__ = (
        "_items",
        "_help",
        '_display',
    )

    def __init__(self, items):
        """
        @param items: items to be enumerated
        @type items: dict or list of tuples
            {key: (human readable text, (helper text))}
            [(key, human readable text, (helper text)), (...)]
        """
        self._items = {}
        self._help = {}
        self._display = {}

        for key in items:
            try:
                value = items[key]
            except (IndexError, TypeError):
                try:
                    help_text = key[2]
                except IndexError:
                    pass
                try:
                    display_text = key[3]
                except IndexError:
                    pass
                value = key[1]
                key = key[0]

            if key in self._items:
                raise ValueError("Duplicite item: %s" % key)
            if isinstance(value, tuple):
                self._help[key] = value[1]
                self._items[key] = value[0]
            else:
                self._items[key] = value
                try:
                    self._help[key] = help_text
                except NameError:
                    pass
                try:
                    self._display[key] = display_text
                except NameError:
                    pass

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, key):
        return self._items[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except (IndexError, KeyError):
            return default

    def get_help(self, key):
        return self._help[key]

    def display(self, key):
        return self._display[key]

    def get_mapping(self):
        """Return list of (key, value) mappings."""
        return self._items.items()

    def get_display_mapping(self):
        """Return list of (key, value) mappings with nicer values."""
        return zip(self._items.values(), self._display.values())

    def list_keys(self, values=None):
        """ [values] -> [keys] or -> all [keys] """
        if values is not None:
            return [self.get_key(value) for value in values]
        else:
            return self._items.keys()

    def get_key(self, value):
        return filter(lambda x: x[1] == value,
                      self._items.items())[0][0]


def test():
    assert Enum({'k': ('key', 'blablabla')})['k'] == 'key'
    assert Enum([('k', 'key', 'blablabla')])['k'] == 'key'
    assert Enum({'k': ('key', 'blablabla')}).get_help('k') == 'blablabla'
    assert Enum([('k', 'key', 'blablabla')]).get_help('k') == 'blablabla'
    assert Enum({'k': 'key'})['k'] == 'key'
    assert Enum({'k': 'key'}).get_key('key') == 'k'
    assert Enum([('k', 'key', 'long key', 'nice key')]).display('k') == 'nice key'

if __name__ == '__main__':
    test()
