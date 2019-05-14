##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import doctest
import os
import re
import shutil
import tempfile
import unittest

import zc.buildout.testing
from zc.buildout.testing import mkdir, write, system
import zope.testing.renormalizing


SETUP_PY = """\
from setuptools import setup
setup(name = "bugfix1")
"""


BUILDOUT_CFG = """\
[buildout]
develop = bugfix1
parts = testbugfix1
offline = true
[testbugfix1]
recipe = zc.recipe.testrunner
eggs =
    bugfix1
script = test
working-directory = sample_working_dir
"""


TESTS_PY = """\
import unittest
class Layer1(object):
    pass
class Layer2(object):
    pass
class TestDemo1(unittest.TestCase):
    def test(self):
        pass
class TestDemo2(unittest.TestCase):
    def test(self):
        pass

def test_suite():
    suite = unittest.TestSuite()
    suite1 = unittest.makeSuite(TestDemo1)
    suite1.layer = Layer1
    suite.addTest(suite1)
    suite2 = unittest.makeSuite(TestDemo2)
    suite2.layer = Layer2
    suite.addTest(suite2)
    return suite
"""


OUTPUT_COMP = """\
Running tests at level 1
Running .EmptyLayer tests:
Set up .EmptyLayer
Running bugfix1.tests.Layer1 tests:
Running in a subprocess.
Set up bugfix1.tests.Layer1 in
Ran 1 tests with 0 failures, 0 errors and 0 skipped in
Tear down bugfix1.tests.Layer1 in
Running bugfix1.tests.Layer2 tests:
Running in a subprocess.
Set up bugfix1.tests.Layer2 in
Ran 1 tests with 0 failures, 0 errors and 0 skipped in
Tear down bugfix1.tests.Layer2 in
Tearing down left over layers:
Tear down .EmptyLayer in
Total: 2 tests, 0 failures, 0 errors and 0 skipped in
"""


class AbsPathTest(unittest.TestCase):
    """Since version 3.6.0 zope.testing can run layers in parallel
    processes. zc.recipe.testrunner sets the working directory for each
    using a relative path. The subprocesses have the given working
    directory already set, but zc.recipe.testrunner tried to set it again
    and failed ("IOError: No such file or directory").
    """

    def setUp(self):
        self.location = os.getcwd()

        # Here we build a sample buildout
        self.tmp = tempfile.mkdtemp(prefix='sample-buildout')
        write(self.tmp, 'buildout.cfg', BUILDOUT_CFG)
        mkdir(self.tmp, 'sample_working_dir')
        mkdir(self.tmp, 'bugfix1')
        mkdir(self.tmp, 'bugfix1', 'bugfix1')
        write(self.tmp, 'bugfix1', 'bugfix1', '__init__.py', '')
        write(self.tmp, 'bugfix1', 'bugfix1', 'tests.py', TESTS_PY)
        write(self.tmp, 'bugfix1', 'setup.py', SETUP_PY)
        write(self.tmp, 'bugfix1', 'README.rst', '')

        os.chdir(self.tmp)
        zc.buildout.buildout.Buildout(
            'buildout.cfg',
            [('buildout', 'log-level', 'WARNING')]
        ).init('fake-argument')

    def tearDown(self):
        os.chdir(self.location)
        shutil.rmtree(self.tmp)

    def runTest(self):
        output = system(os.path.join(self.tmp, 'bin', 'test') + ' -vv -j2')
        comp_lines = OUTPUT_COMP.split('\n')

        # Here we check if meaningful outputs have been given. See above.
        self.assertTrue(OUTPUT_COMP)
        self.assertTrue(comp_lines)
        for line in comp_lines:
            self.assertIn(line, output)


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install('six', test)
    zc.buildout.testing.install_develop('zc.recipe.testrunner', test)
    zc.buildout.testing.install_develop('zc.recipe.egg', test)
    zc.buildout.testing.install('zope.testing', test)
    zc.buildout.testing.install('zope.testrunner', test)
    zc.buildout.testing.install('zope.interface', test)
    zc.buildout.testing.install('zope.exceptions', test)


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'README.rst',
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            checker=zope.testing.renormalizing.RENormalizing(
                [
                    zc.buildout.testing.normalize_path,
                    zc.buildout.testing.normalize_script,
                    zc.buildout.testing.normalize_egg_py,
                    zc.buildout.testing.normalize_endings,
                    (re.compile(r'#!\S+py\S*'), '#!python'),
                    (re.compile(r'\d[.]\d+ seconds'), '0.001 seconds'),
                    (re.compile(r'\d[.]\d+ s'), '0.001 s'),
                    (re.compile('zope.testing-[^-]+-'), 'zope.testing-X-'),
                    (re.compile('zope.testrunner-[^-]+-'),
                     'zope.testrunner-X-'),
                    (re.compile('setuptools-[^-]+-'), 'setuptools-X-'),
                    (re.compile('distribute-[^-]+-'), 'setuptools-X-'),
                    (re.compile('zope.interface-[^-]+-'),
                     'zope.interface-X-'),
                    (re.compile(r'zope.exceptions-[^-]+-.*\.egg'),
                        'zope.exceptions-X-pyN.N.egg'),
                    # windows happiness for ``extra-paths``:
                    (re.compile(
                        r'[a-zA-Z]:\\\\usr\\\\local\\\\zope\\\\lib\\\\python'),
                     '/usr/local/zope/lib/python'),
                    # windows happiness for ``working-directory``:
                    (re.compile(r'[a-zA-Z]:\\\\foo\\\\bar'), '/foo/bar'),
                    # more windows happiness:
                    (re.compile(r'eggs\\\\'), 'eggs/'),
                    (re.compile(r'parts\\\\'), 'parts/')]
            ),
        ), (AbsPathTest())
    ))
