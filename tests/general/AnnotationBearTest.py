import unittest
from queue import Queue

from coalib.settings.Setting import Setting
from bears.general.AnnotationBear import AnnotationBear
from coalib.results.SourceRange import SourceRange
from coalib.settings.Section import Section
from tests.LocalBearTestHelper import execute_bear


class AnnotationBearTest(unittest.TestCase):

    def setUp(self):
        self.section = Section("")
        self.section.append(Setting('language', 'c'))
        self.section.append(Setting('language_family', 'c'))

    def assertRange(self, file, uut, sourcerange):
        with execute_bear(uut, "filename", file) as results:
            print("results", results)
            for result in results:
                for code in result.contents:
                    self.assertEqual(code.start.line, sourcerange.start.line)
                    self.assertEqual(code.start.column,
                                     sourcerange.start.column)
                    self.assertEqual(code.end.line, sourcerange.end.line)
                    self.assertEqual(code.end.column, sourcerange.end.column)
            self.assertNotEqual(results, [])

    def assertEmpty(self, file, uut):
        with execute_bear(uut, "filename", file) as results:
            for result in results:
                self.assertEqual([], result.contents)

    def test_comments(self):
        file = """comments\n/*in line2*/,  \n"""
        uut = AnnotationBear(self.section, Queue())
        sourcerange = SourceRange.from_values("filename", 2, 1, 2, 13)
        self.assertRange(file, uut, sourcerange)

        file = """comments \n/*"then a string in comment"*/"""
        sourcerange = SourceRange.from_values("filename", 2, 1, 2, 31)
        self.assertRange(file, uut, sourcerange)

        file = """ this line has a //comment """
        sourcerange = SourceRange.from_values("filename", 1, 18, 1, 29)
        self.assertRange(file, uut, sourcerange)

        file = """ this is a //comment 'has a string' \n nextline """
        sourcerange = SourceRange.from_values("filename", 1, 12, 1, 37)
        self.assertRange(file, uut, sourcerange)

        file = """ i have a comment /* and a //comment inside a comment*/ """
        sourcerange = SourceRange.from_values("filename", 1, 19, 1, 56)
        self.assertRange(file, uut, sourcerange)

    def test_string(self):
        section = Section("")
        section.append(Setting('language', 'python3'))
        section.append(Setting('language_family', 'python3'))
        uut = AnnotationBear(section, Queue())
        file = """ strings: "only string" """
        sourcerange = SourceRange.from_values("filename", 1, 11, 1, 24)
        self.assertRange(file, uut, sourcerange)

        file = """ strings: " #then a comment in string" """
        sourcerange = SourceRange.from_values("filename", 1, 11, 1, 39)
        self.assertRange(file, uut, sourcerange)

        file = ' """Trying a multinline string""" '
        sourcerange = SourceRange.from_values("filename", 1, 2, 1, 34)
        self.assertRange(file, uut, sourcerange)

        file = """ i have a string: " and a 'string' inside a string" """
        sourcerange = SourceRange.from_values("filename", 1, 19, 1, 52)
        self.assertRange(file, uut, sourcerange)

        file = """ i have a string: " and a ''' multinline string'''
                   inside a string" """
        sourcerange = SourceRange.from_values("filename", 1, 19, 1, 60)

    def test_none(self):
        file = """no string or comments"""
        uut = AnnotationBear(self.section, Queue())
        self.assertEmpty(file, uut)
