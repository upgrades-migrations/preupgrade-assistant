# -*- coding: utf-8 -*-

import shutil
import unittest
import tempfile
import preupg

from xml.etree import ElementTree
from preupg.application import Application
from preupg.conf import DummyConf, Conf
from preupg.ui.report.processing import xml_to_html, stringify_children, parse_xml_report
from preupg.ui.report.service import extract_tarball

from django.test import TestCase


class TestXML(TestCase):

    def test_to_html(self):
        links = """\
Prefix <html:a xmlns:html="http://www.w3.org/1999/xhtml/" \
href="./dirtyconf/">dirtyconf/</html:a> suffix. \
Another link <html:a xmlns:html="http://www.w3.org/1999/xhtml/" \
href="./kickstart/noverifycfg/">kickstart/noverifycfg/</html:a> ."""

        b = """\
Prefix <html:b xmlns:html="http://www.w3.org/1999/xhtml/">\
bold text</html:b> suffix."""

        expected_links = """\
Prefix <a href="__INSERT_URL__?path=dirtyconf/" target="_blank">dirtyconf/</a> suffix. \
Another link <a href="__INSERT_URL__?path=kickstart/noverifycfg/" target="_blank">kickstart/noverifycfg/</a> ."""

        expected_b = "Prefix <b>bold text</b> suffix."

        got_links = xml_to_html(links)
        got_b = xml_to_html(b)

        self.assertEqual(got_links, expected_links)
        self.assertEqual(got_b, expected_b)

    def test_stringify_children(self):
        node = ElementTree.fromstring("""<content xmlns:html="http://www.w3.org/1999/xhtml"> \
Text outside tag <html:div>Text <html:em>inside</html:em> tag</html:div> x <b>y</b> z asd\
</content>""")
        r = stringify_children(node).strip()
        expected_r = 'Text outside tag <div>Text <em>inside</em> tag</div> x <b>y</b> z asd'
        self.assertEqual(r, expected_r)

        node2 = ElementTree.fromstring("""<x xmlns:html="http://www.w3.org/1999/xhtml"> \
<html:y>a</html:y></x>""")
        r2 = stringify_children(node2).strip()
        self.assertEqual(r2, '<y>a</y>')

        node3 = ElementTree.fromstring("""<x xmlns:html="http://www.w3.org/1999/xhtml"> a \
<html:y>t<html:y2>a</html:y2>y</html:y>y</x>""")
        r3 = stringify_children(node3).strip()
        self.assertEqual(r3, 'a <y>t<y2>a</y2>y</y>y')


# class TestImport(TestCase):
#     def setUp(self):
#         self.temp_dir = tempfile.mkdtemp()
#         conf = {
#             "contents": "tests/RHEL6_7/dummy_preupg/all-xccdf.xml",
#             "profile": "xccdf_preupg_profile_default",
#             "result_dir": self.temp_dir,
#             "skip_common": True,
#             "temp_dir": self.temp_dir,
#             "debug": True,  # so root check won't fail
#         }
#         self.conf = DummyConf(**conf)
#
#     def tearDown(self):
#         shutil.rmtree(self.temp_dir)
#
#     def test_report_import(self):
#         """
#         "scan" system with dummy content and import it
#         """
#         a = Application(Conf(self.conf, preupg.settings))
#         tarball_path = a.scan_system()
#
#         xml_path, html_path = extract_tarball(tarball_path, self.temp_dir)
#         self.assertTrue(len(parse_xml_report(xml_path)) > 0)


if __name__ == '__main__':
    unittest.main()
