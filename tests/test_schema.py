##############################################################################
#
# Copyright (c) 2002, 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests of ZConfig schemas."""

import StringIO
import unittest

import ZConfig

from ZConfig.loader import ConfigLoader
from ZConfig.url import urljoin
from ZConfig.tests.test_config import CONFIG_BASE


def uppercase(value):
    return str(value).upper()

def appsection(value):
    return MySection(value)

class MySection:
    def __init__(self, value):
        self.conf = value
        self.length = len(value)


class BaseSchemaTest(unittest.TestCase):
    """Utility methods which can be used with the schema support."""

    def load_both(self, schema_url, conf_url):
        schema = self.load_schema(schema_url)
        conf = self.load_config(schema, conf_url)
        return schema, conf

    def load_schema(self, relurl):
        self.url = urljoin(CONFIG_BASE, relurl)
        self.schema = ZConfig.loadSchema(self.url)
        self.assert_(self.schema.issection())
        return self.schema

    def load_schema_text(self, text):
        sio = StringIO.StringIO(text)
        self.schema = ZConfig.loadSchemaFile(sio)
        return self.schema

    def load_config(self, schema, conf_url, num_handlers=0):
        conf_url = urljoin(CONFIG_BASE, conf_url)
        self.conf, self.handlers = ConfigLoader(schema).loadURL(conf_url)
        self.assertEqual(len(self.handlers), num_handlers)
        return self.conf

    def load_config_text(self, schema, text, num_handlers=0):
        sio = StringIO.StringIO(text)
        self.conf, self.handlers = ZConfig.loadConfigFile(schema, sio)
        self.assertEqual(len(self.handlers), num_handlers)
        return self.conf


class SchemaTestCase(BaseSchemaTest):
    """Tests of the basic schema support itself."""

    def test_minimal_schema(self):
        schema = self.load_schema_text("<schema/>")
        self.assertEqual(len(schema), 0)
        self.assertEqual(schema.getchildnames(), [])
        self.assertRaises(IndexError,
                          lambda schema=schema: schema[0])
        self.assertRaises(ZConfig.ConfigurationError,
                          schema.getinfo, "foo")

    def test_simple(self):
        schema, conf = self.load_both("simple.xml", "simple.conf")
        eq = self.assertEqual
        eq(conf.var1, 'abc')
        eq(conf.int_var, 12)
        eq(conf.float_var, 12.02)
        eq(conf.neg_int, -2)

        check = self.assert_
        check(conf.true_var_1)
        check(conf.true_var_2)
        check(conf.true_var_3)
        check(not conf.false_var_1)
        check(not conf.false_var_2)
        check(not conf.false_var_3)

    def test_app_datatype(self):
        dtname = __name__ + ".uppercase"
        schema = self.load_schema_text(
            "<schema>"
            "  <key name='a' datatype='%s'/>"
            "  <key name='b' datatype='%s' default='abc'/>"
            "  <multikey name='c' datatype='%s'>"
            "    <default>abc</default>"
            "    <default>abc</default>"
            "    </multikey>"
            "  <multikey name='d' datatype='%s'>"
            "    <default>not</default>"
            "    <default>lower</default>"
            "    <default>case</default>"
            "    </multikey>"
            "</schema>"
            % (dtname, dtname, dtname, dtname))
        conf = self.load_config_text(schema,
                                     "a qwerty\n"
                                     "c upp\n"
                                     "c er \n"
                                     "c case\n")
        eq = self.assertEqual
        eq(conf.a, 'QWERTY')
        eq(conf.b, 'ABC')
        eq(conf.c, ['UPP', 'ER', 'CASE'])
        eq(conf.d, ['NOT', 'LOWER', 'CASE'])

    def test_app_sectiontype(self):
        schema = self.load_schema_text(
            "<schema datatype='.appsection' prefix='%s'>"
            "  <sectiontype type='foo' datatype='.MySection'>"
            "    <key name='sample' datatype='integer' default='345'/>"
            "    </sectiontype>"
            "  <section name='sect' type='foo' />"
            "</schema>"
            % __name__)
        conf = self.load_config_text(schema,
                                     "<foo sect>\n"
                                     "  sample 42\n"
                                     "</foo>")
        self.assert_(isinstance(conf, MySection))
        self.assertEqual(conf.length, 1)
        o1 = conf.conf[0]
        self.assert_(isinstance(o1, MySection))
        self.assertEqual(o1.length, 1)
        self.assertEqual(o1.conf.sample, 42)
        o2 = conf.conf.sect
        self.assert_(o1 is o2)

    def test_empty_sections(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <sectiontype type='section'/>"
            "  <section type='section' name='s1'/>"
            "  <section type='section' name='s2'/>"
            "</schema>")
        conf = self.load_config_text(schema,
                                     "<section s1>\n"
                                     "</section>\n"
                                     "<section s2/>")
        self.assert_(conf.s1 is not None)
        self.assert_(conf.s2 is not None)

    def test_deeply_nested_sections(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <sectiontype type='type1'>"
            "    <key name='key' default='type1-value'/>"
            "    </sectiontype>"
            "  <sectiontype type='type2'>"
            "    <key name='key' default='type2-value'/>"
            "    <section name='sect' type='type1'/>"
            "    </sectiontype>"
            "  <sectiontype type='type3'>"
            "    <key name='key' default='type3-value'/>"
            "    <section name='sect' type='type2'/>"
            "    </sectiontype>"
            "  <section name='sect' type='type3'/>"
            "</schema>")
        conf = self.load_config_text(schema,
                                     "<type3 sect>\n"
                                     "  key sect3-value\n"
                                     "  <type2 sect>\n"
                                     "    key sect2-value\n"
                                     "    <type1 sect/>\n"
                                     "  </type2>\n"
                                     "</type3>")
        eq = self.assertEqual
        eq(conf.sect.sect.sect.key, "type1-value")
        eq(len(conf.sect.sect.sect), 1)
        eq(conf.sect.sect.key, "sect2-value")
        eq(len(conf.sect.sect), 2)
        eq(conf.sect.key, "sect3-value")
        eq(len(conf.sect), 2)

    def test_multivalued_keys(self):
        schema = self.load_schema_text(
            "<schema handler='def'>"
            "  <multikey name='a' handler='ABC' />"
            "  <multikey name='b' datatype='integer'>"
            "    <default>1</default>"
            "    <default>2</default>"
            "  </multikey>"
            "  <multikey name='c' datatype='integer'>"
            "    <default>3</default>"
            "    <default>4</default>"
            "    <default>5</default>"
            "  </multikey>"
            "  <multikey name='d' />"
            "</schema>")
        conf = self.load_config_text(schema,
                                     "a foo\n"
                                     "a bar\n"
                                     "c 41\n"
                                     "c 42\n"
                                     "c 43\n",
                                     num_handlers=2)
        L = []
        self.handlers({'abc': L.append,
                       'DEF': L.append})
        self.assertEqual(L, [['foo', 'bar'], conf])
        L = []
        self.handlers({'abc': None,
                       'DEF': L.append})
        self.assertEqual(L, [conf])
        self.assertEqual(conf.a, ['foo', 'bar'])
        self.assertEqual(conf.b, [1, 2])
        self.assertEqual(conf.c, [41, 42, 43])
        self.assertEqual(conf.d, [])

    def test_key_default_element(self):
        self.assertRaises(ZConfig.SchemaError, self.load_schema_text,
                          "<schema>"
                          "  <key name='name'>"
                          "    <default>text</default>"
                          "  </key>"
                          "</schema>")

    def test_bad_handler_maps(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <key name='a' handler='abc'/>"
            "  <key name='b' handler='def'/>"
            "</schema>")
        conf = self.load_config_text(schema, "a foo\n b bar",
                                     num_handlers=2)
        self.assertRaises(ZConfig.ConfigurationError,
                          self.handlers, {'abc': id, 'ABC': id, 'def': id})
        self.assertRaises(ZConfig.ConfigurationError,
                          self.handlers, {})

    def test_handler_ordering(self):
        schema = self.load_schema_text(
            "<schema handler='c'>"
            "  <sectiontype type='inner'>"
            "  </sectiontype>"
            "  <sectiontype type='outer'>"
            "    <section type='inner' name='sect-inner' handler='a'/>"
            "  </sectiontype>"
            "  <section type='outer' name='sect-outer' handler='b'/>"
            "</schema>")
        conf = self.load_config_text(schema,
                                     "<outer sect-outer>\n"
                                     "  <inner sect-inner/>\n"
                                     "</outer>",
                                     num_handlers=3)
        L = []
        self.handlers({'a': L.append,
                       'b': L.append,
                       'c': L.append})
        outer = conf.sect_outer
        inner = outer.sect_inner
        self.assertEqual(L, [inner, outer, conf])

    def test_duplicate_section_names(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <sectiontype type='sect'/>"
            "  <sectiontype type='nesting'>"
            "    <section name='a' type='sect'/>"
            "    </sectiontype>"
            "  <section name='a' type='nesting'/>"
            "</schema>")
        self.assertRaises(ZConfig.ConfigurationError,
                          self.load_config_text,
                          schema, "<sect a/>\n<sect a/>\n")
        conf = self.load_config_text(schema,
                                     "<nesting a>\n"
                                     "  <sect a/>\n"
                                     "</nesting>")

    def test_disallowed_duplicate_attribute(self):
        self.assertRaises(ZConfig.SchemaError,
                          self.load_schema_text,
                          "<schema>"
                          "  <key name='a'/>"
                          "  <key name='b' attribute='a'/>"
                          "</schema>")

    def test_unknown_datatype_name(self):
        self.assertRaises(ZConfig.SchemaError,
                          self.load_schema_text, "<schema datatype='foobar'/>")

    def test_load_sectiongroup(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <sectiongroup type='group'>"
            "    <sectiontype type='t1'>"
            "      <key name='k1' default='default1'/>"
            "      </sectiontype>"
            "    <sectiontype type='t2'>"
            "      <key name='k2' default='default2'/>"
            "      </sectiontype>"
            "    </sectiongroup>"
            "  <multisection name='*' type='group' attribute='g'/>"
            "</schema>")
        # check the types that get defined
        t = schema.gettype("group")
        self.assert_(t.istypegroup())
        t1 = schema.gettype("t1")
        self.assert_(not t1.istypegroup())
        self.assert_(t.getsubtype("t1") is t1)
        t2 = schema.gettype("t2")
        self.assert_(not t2.istypegroup())
        self.assert_(t.getsubtype("t2") is t2)
        self.assertRaises(ZConfig.ConfigurationError, t.getsubtype, "group")
        self.assert_(t1 is not t2)
        # try loading a config that relies on this schema
        conf = self.load_config_text(schema,
                                     "<t1/>\n"
                                     "<t1>\n k1 value1\n </t1>\n"
                                     "<t2/>\n"
                                     "<t2>\n k2 value2\n </t2>\n")
        eq = self.assertEqual
        eq(len(conf.g), 4)
        eq(conf.g[0].k1, "default1")
        eq(conf.g[1].k1, "value1")
        eq(conf.g[2].k2, "default2")
        eq(conf.g[3].k2, "value2")

        # white box:
        self.assert_(conf.g[0]._type is t1)
        self.assert_(conf.g[1]._type is t1)
        self.assert_(conf.g[2]._type is t2)
        self.assert_(conf.g[3]._type is t2)

    def test_sectiongroup_extension(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <sectiongroup type='group'/>"
            "  <sectiontype type='extra' group='group'/>"
            "  <section name='thing' type='group'/>"
            "</schema>")
        group = schema.gettype("group")
        self.assert_(schema.gettype("extra") is group.getsubtype("extra"))

        # make sure we can use the extension in a config:
        conf = self.load_config_text(schema, "<extra thing/>")
        self.assertEqual(conf.thing.getSectionType(), "extra")

    def test_sectiongroup_extension_errors(self):
        # specifying a non-existant group
        self.assertRaises(ZConfig.SchemaError, self.load_schema_text,
                          "<schema>"
                          "  <sectiontype type='s' group='group'/>"
                          "</schema>")
        # specifying something that isn't a group
        self.assertRaises(ZConfig.SchemaError, self.load_schema_text,
                          "<schema>"
                          "  <sectiontype type='t1'/>"
                          "  <sectiontype type='t2' group='t1'/>"
                          "</schema>")
        # specifying a group from w/in a group
        self.assertRaises(ZConfig.SchemaError, self.load_schema_text,
                          "<schema>"
                          "  <sectiongroup type='group'>"
                          "    <sectiontype type='t' group='group'/>"
                          "  </sectiongroup>"
                          "</schema>")

    def test_arbitrary_key(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <key name='+' required='yes' attribute='keymap'"
            "       datatype='integer'/>"
            "</schema>")
        conf = self.load_config_text(schema, "some-key 42")
        self.assertEqual(conf.keymap, {'some-key': 42})

    def test_arbitrary_multikey(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <multikey name='+' required='yes' attribute='keymap'"
            "            datatype='integer'/>"
            "</schema>")
        conf = self.load_config_text(schema, "some-key 42\n some-key 43")
        self.assertEqual(conf.keymap, {'some-key': [42, 43]})

    def test_arbitrary_keys_with_others(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <key name='k1' default='v1'/>"
            "  <key name='k2' default='2' datatype='integer'/>"
            "  <key name='+' required='yes' attribute='keymap'"
            "       datatype='integer'/>"
            "</schema>")
        conf = self.load_config_text(schema, "some-key 42 \n k2 3")
        self.assertEqual(conf.k1, 'v1')
        self.assertEqual(conf.k2, 3)
        self.assertEqual(conf.keymap, {'some-key': 42})

    def test_arbitrary_key_missing(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <key name='+' required='yes' attribute='keymap' />"
            "</schema>")
        self.assertRaises(ZConfig.ConfigurationError,
                          self.load_config_text, schema, "# empty config file")

    def test_arbitrary_key_bad_schema(self):
        self.assertRaises(ZConfig.SchemaError,
                          self.load_schema_text,
                          "<schema>"
                          "  <key name='+' attribute='attr1'/>"
                          "  <key name='+' attribute='attr2'/>"
                          "</schema>")

    def test_getrequiredtypes(self):
        schema = self.load_schema("library.xml")
        self.assertEqual(schema.getrequiredtypes(), [])

        schema = self.load_schema_text(
            "<schema type='top'>"
            "  <sectiontype type='used'/>"
            "  <sectiontype type='unused'/>"
            "  <section type='used' name='a'/>"
            "</schema>")
        L = schema.getrequiredtypes()
        L.sort()
        self.assertEqual(L, ["top", "used"])

    def test_getunusedtypes(self):
        schema = self.load_schema("library.xml")
        L = schema.getunusedtypes()
        L.sort()
        self.assertEqual(L, ["type-a", "type-b"])

        schema = self.load_schema_text(
            "<schema type='top'>"
            "  <sectiontype type='used'/>"
            "  <sectiontype type='unused'/>"
            "  <section type='used' name='a'/>"
            "</schema>")
        self.assertEqual(schema.getunusedtypes(), ["unused"])

    def test_section_value_mutation(self):
        schema, conf = self.load_both("simple.xml", "simple.conf")
        orig = conf.empty
        new = []
        conf.empty = new
        self.assert_(conf[0] is new)

    def test_simple_anonymous_section(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <sectiontype type='sect'>"
            "    <key name='key' default='value'/>"
            "  </sectiontype>"
            "  <section name='*' type='sect' attribute='attr'/>"
            "</schema>")
        conf = self.load_config_text(schema, "<sect/>")
        self.assertEqual(conf.attr.key, "value")

    def test_simple_anynamed_section(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <sectiontype type='sect'>"
            "    <key name='key' default='value'/>"
            "  </sectiontype>"
            "  <section name='+' type='sect' attribute='attr'/>"
            "</schema>")
        conf = self.load_config_text(schema, "<sect name/>")
        self.assertEqual(conf.attr.key, "value")
        self.assertEqual(conf.attr.getSectionName(), "name")

        # if we omit the name, it's an error
        self.assertRaises(ZConfig.ConfigurationError,
                          self.load_config_text, schema, "<sect/>")

    def test_nested_abstract_sectiontype(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <sectiongroup type='abstract'>"
            "    <sectiontype type='t1'/>"
            "    <sectiontype type='t2'>"
            "      <section type='abstract' name='s1'/>"
            "    </sectiontype>"
            "  </sectiongroup>"
            "  <section type='abstract' name='*' attribute='s2'/>"
            "</schema>")
        conf = self.load_config_text(schema, "<t2>\n <t1 s1/>\n</t2>")

    def test_reserved_attribute_prefix(self):
        template = ("<schema>\n"
                    "  <sectiontype type='s'/>\n"
                    "  %s\n"
                    "</schema>")
        def check(thing, self=self, template=template):
            text = template % thing
            self.assertRaises(ZConfig.SchemaError,
                              self.load_schema_text, text)

        check("<key name='a' attribute='getSection'/>")
        check("<key name='a' attribute='getSectionThing'/>")
        check("<multikey name='a' attribute='getSection'/>")
        check("<multikey name='a' attribute='getSectionThing'/>")
        check("<section type='s' name='*' attribute='getSection'/>")
        check("<section type='s' name='*' attribute='getSectionThing'/>")
        check("<multisection type='s' name='*' attribute='getSection'/>")
        check("<multisection type='s' name='*' attribute='getSectionThing'/>")

    def test_sectiontype_as_schema(self):
        schema = self.load_schema_text(
            "<schema>"
            "  <sectiontype type='s'>"
            "    <key name='skey' default='skey-default'/>"
            "  </sectiontype>"
            "  <sectiontype type='t'>"
            "    <key name='tkey' default='tkey-default'/>"
            "    <section name='*' type='s' attribute='section'/>"
            "  </sectiontype>"
            "</schema>")
        t = schema.gettype("t")
        conf = self.load_config_text(t, "<s/>")
        self.assertEqual(conf.tkey, "tkey-default")
        self.assertEqual(conf.section.skey, "skey-default")


def test_suite():
    return unittest.makeSuite(SchemaTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
