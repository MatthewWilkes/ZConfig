"""Top-level configuration handle."""

import os
import urllib
import urllib2
import urlparse

import ZConfig

from Config import Configuration, ImportingConfiguration
from Substitution import isname, substitute


class Context:

    def __init__(self):
        self._imports = []         # URL  -> Configuration
        self._named_sections = {}  # name -> Configuration
        self._needed_names = {}    # name -> [needy Configuration, ...]
        self._current_imports = []
        self._all_sections = []

    # subclass-support API

    def createImportedSection(self, section, url):
        return ImportingConfiguration(url)

    def createNestedSection(self, section, type, name, delegatename):
        if name:
            name = name.lower()
        return Configuration(section, type.lower(), name, section.url)

    def createToplevelSection(self, url):
        return ImportingConfiguration(url)

    def createResource(self, file, url):
        return Resource(file, url)

    def getDelegateType(self, type):
        # Applications must provide delegation typing information by
        # overriding the Context.getDelegateType() method.
        return type.lower()

    def parse(self, resource, section):
        from ApacheStyle import Parse
        Parse(resource, self, section)

    def _normalize_url(self, url):
        if os.path.exists(url):
            url = "file://" + urllib.pathname2url(os.path.abspath(url))
        else:
            parts = urlparse.urlparse(url)
            if not parts[0]:
                raise ValueError("invalid URL, or file does not exist:\n"
                                 + repr(url))
        return url

    # public API

    def load(self, url):
        """Load a resource from a URL or pathname."""
        url = self._normalize_url(url)
        top = self.createToplevelSection(url)
        self._all_sections.append(top)
        self._imports = [top]
        self._parse_url(url, top)
        self._finish()
        return top

    loadURL = load # Forward-compatible alias

    def loadfile(self, file, url=None):
        if not url:
            name = getattr(file, "name", None)
            if name and name[0] != "<" and name[-1] != ">":
                url = "file://" + urllib.pathname2url(os.path.abspath(name))
        top = self.createToplevelSection(url)
        self._all_sections.append(top)
        self._imports = [top]
        self._current_imports.append(top)
        r = self.createResource(file, url)
        try:
            self.parse(r, top)
        finally:
            del self._current_imports[-1]
        self._finish()
        return top

    loadFile = loadfile # Forward-compatible alias


    # interface for parser

    def importConfiguration(self, section, url):
        for config in self._imports:
            if config.url == url:
                return config
        newsect = self.createImportedSection(section, url)
        self._all_sections.append(newsect)
        self._imports.append(newsect)
        section.addImport(newsect)
        self._parse_url(url, newsect)

    def includeConfiguration(self, section, url):
        # XXX we always re-parse, unlike import
        file = urllib2.urlopen(url)
        r = self.createResource(file, url)
        try:
            self.parse(r, section)
        finally:
            file.close()

    def nestSection(self, section, type, name, delegatename):
        if name:
            name = name.lower()
        type = type.lower()
        if name and self._named_sections.has_key(name):
            # Make sure sections of the same name are not defined
            # twice in the same resource, and that once a name has
            # been defined, its type is not changed by a section from
            # another resource.
            oldsect = self._named_sections[name]
            if oldsect.url == section.url:
                raise ZConfig.ConfigurationError(
                    "named section cannot be defined twice in same resource")
            if oldsect.type != type:
                raise ZConfig.ConfigurationError(
                    "named section cannot change type")
        newsect = self.createNestedSection(section, type, name, delegatename)
        self._all_sections.append(newsect)
        if delegatename:
            # The knitting together of the delegation graph needs this.
            try:
                L = self._needed_names[delegatename]
            except KeyError:
                L = []
                self._needed_names[delegatename] = L
            L.append(newsect)
        section.addChildSection(newsect)
        if name:
            self._named_sections[name] = newsect
            current = self._current_imports[-1]
            if section is not current:
                current.addNamedSection(newsect)
            for config in self._current_imports[:-1]:
                # XXX seems very painful
                if not config._sections_by_name.has_key((type, name)):
                    config.addNamedSection(newsect)
        return newsect

    # internal helpers

    def _parse_url(self, url, section):
        url, fragment = urlparse.urldefrag(url)
        if fragment:
            raise ZConfig.ConfigurationError(
                "fragment identifiers are not currently supported")
        file = urllib2.urlopen(url)
        self._current_imports.append(section)
        r = self.createResource(file, url)
        try:
            self.parse(r, section)
        finally:
            del self._current_imports[-1]
            file.close()

    def _finish(self):
        # Resolve section delegations
        for name, L in self._needed_names.items():
            section = self._named_sections[name]
            for referrer in L:
                type = self.getDelegateType(referrer.type)
                if type is None:
                    raise ZConfig.ConfigurationTypeError(
                        "%s sections are not allowed to specify delegation\n"
                        "(in %s)"
                        % (repr(referrer.type), referrer.url),
                        referrer.type, None)
                type = type.lower()
                if type != section.type:
                    raise ZConfig.ConfigurationTypeError(
                        "%s sections can only inherit from %s sections\n"
                        "(in %s)"
                        % (repr(referrer.type), repr(type), referrer.url),
                        referrer.type, type)
                referrer.setDelegate(section)
        self._needed_names = None
        # Now "finish" the sections, making sure we close inner
        # sections before outer sections.  We really should order
        # these better, but for now, "finish" all sections that have
        # no delegates first, then those that have them.  This is not
        # enough to guarantee that delegates are finished before their
        # users.
        self._all_sections.reverse()
        for sect in self._all_sections:
            if sect.delegate is None:
                sect.finish()
        for sect in self._all_sections:
            if sect.delegate is not None:
                sect.finish()
        self._all_sections = None


class Resource:
    def __init__(self, file, url):
        self.file = file
        self.url = url
        self._definitions = {}

    def define(self, name, value):
        key = name.lower()
        if self._definitions.has_key(key):
            raise ZConfig.ConfigurationError("cannot redefine " + `name`)
        if not isname(name):
            raise ZConfig.ConfigurationError(
                "not a substitution legal name: " + `name`)
        self._definitions[key] = value

    def substitute(self, s):
        # XXX  I don't really like calling this substitute(),
        # XXX  but it will do for now.
        return substitute(s, self._definitions)
