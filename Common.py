"""Names used from all modules in the package.

Since some names are only defined if needed, this module should be
imported using the from-import-* syntax.
"""

try:
    True
except NameError:
    True = 1
    False = 0


class ConfigurationError(Exception):
    def __init__(self, msg):
        self.message = msg
        Exception.__init__(self, msg)

    def __str__(self):
        return self.message


class ConfigurationMissingSectionError(ConfigurationError):
    def __init__(self, type, name=None):
        self.type = type
        self.name = name
        details = 'Missing section (type: %s' % type
        if name is not None:
            details += ', name: %s' % name
        ConfigurationError.__init__(self, details + ')')


class ConfigurationConflictingSectionError(ConfigurationError):
    def __init__(self, type, name=None):
        self.type = type
        self.name = name
        details = 'Conflicting sections (type: %s' % type
        if name is not None:
            details += ', name: %s' % name
        ConfigurationError.__init__(self, details + ')')


class ConfigurationSyntaxError(ConfigurationError):
    def __init__(self, msg, url, lineno):
        self.url = url
        self.lineno = lineno
        ConfigurationError.__init__(self, msg)

    def __str__(self):
        return "%s\n(line %s in %s)" % (self.message, self.lineno, self.url)


class ConfigurationTypeError(ConfigurationError):
    def __init__(self, msg, found, expected):
        self.found = found
        self.expected = expected
        ConfigurationError.__init__(self, msg)
