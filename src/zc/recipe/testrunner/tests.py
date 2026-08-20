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
import importlib.metadata
import json
import os
import re
import shutil
import tempfile
import unittest

import zc.buildout.testing
import zope.testing.renormalizing
from zc.buildout.testing import mkdir
from zc.buildout.testing import system
from zc.buildout.testing import write

import zc.recipe.testrunner


SETUP_PY = """\
from setuptools import setup
setup(name = "bugfix1")
"""

EXTRAS_SETUP_PY = """\
from setuptools import setup
setup(
    name="extrapkg",
    extras_require={"test": []},
)
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

EXTRAS_BUILDOUT_CFG = """\
[buildout]
develop = extrapkg
parts = testextrapkg
offline = true

[testextrapkg]
recipe = zc.recipe.testrunner
eggs =
    extrapkg[test]
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
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite1 = loader.loadTestsFromTestCase(TestDemo1)
    suite1.layer = Layer1
    suite.addTest(suite1)
    suite2 = loader.loadTestsFromTestCase(TestDemo2)
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


class ExtrasInEggsTest(unittest.TestCase):
    """Eggs with extras like ``extrapkg[test]`` must be resolved correctly.

    ``canonicalize_name('extrapkg[test]')`` produces ``'extrapkg[test]'``
    (with the bracket suffix) which does not match the dist-map key
    ``'extrapkg'``.  The install() method must strip extras before
    canonicalizing.
    """

    def setUp(self):
        self.location = os.getcwd()

        self.tmp = tempfile.mkdtemp(prefix='sample-buildout')
        write(self.tmp, 'buildout.cfg', EXTRAS_BUILDOUT_CFG)
        mkdir(self.tmp, 'sample_working_dir')
        mkdir(self.tmp, 'extrapkg')
        mkdir(self.tmp, 'extrapkg', 'extrapkg')
        write(self.tmp, 'extrapkg', 'extrapkg', '__init__.py', '')
        write(self.tmp, 'extrapkg', 'extrapkg', 'tests.py', TESTS_PY)
        write(self.tmp, 'extrapkg', 'setup.py', EXTRAS_SETUP_PY)
        write(self.tmp, 'extrapkg', 'README.rst', '')

        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.location)
        shutil.rmtree(self.tmp)

    def runTest(self):
        # Building the buildout triggers install() which must handle
        # extras in egg specs.  The bug causes:
        #   ValueError: Requirement not found in working set: extrapkg[test]
        zc.buildout.buildout.Buildout(
            'buildout.cfg',
            [('buildout', 'log-level', 'WARNING')]
        ).init('fake-argument')

        output = system(
            os.path.join(
                self.tmp,
                'bin',
                'test') +
            ' --list-tests')
        self.assertNotIn('Requirement not found', output)
        self.assertNotIn('Error', output)


def make_dist_info(tmp, name='pkg', version='1.0', direct_url=None,
                   pth_lines=None, record=None, pth_name=None):
    """Create a buildout 6 style develop-eggs layout for a develop egg.

    Writes ``develop-eggs/<name>-<version>.dist-info`` with a minimal
    ``METADATA``, optionally ``direct_url.json`` (a dict is serialized as
    JSON, a string is written verbatim), and optionally an accompanying
    ``.pth`` file next to the dist-info, named ``pth_name`` or, by
    default, ``__editable__.<name>-<version>.pth``.

    ``record`` controls the ``RECORD`` file: ``None`` lists all created
    files, ``False`` omits ``RECORD`` entirely (``dist.files is None``),
    and a list is used as explicit entries.

    Returns the ``importlib.metadata.Distribution`` for the dist-info.
    """
    develop_eggs = os.path.join(tmp, 'develop-eggs')
    if not os.path.exists(develop_eggs):
        mkdir(develop_eggs)
    dist_info = f'{name}-{version}.dist-info'
    mkdir(develop_eggs, dist_info)
    write(develop_eggs, dist_info, 'METADATA',
          f'Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n')
    entries = [f'{dist_info}/METADATA']
    if direct_url is not None:
        if isinstance(direct_url, dict):
            direct_url = json.dumps(direct_url)
        write(develop_eggs, dist_info, 'direct_url.json', direct_url)
        entries.append(f'{dist_info}/direct_url.json')
    if pth_lines is not None:
        if pth_name is None:
            pth_name = f'__editable__.{name}-{version}.pth'
        write(develop_eggs, pth_name, '\n'.join(pth_lines) + '\n')
        entries.append(pth_name)
    if record is None:
        record = entries
    if record is not False:
        write(develop_eggs, dist_info, 'RECORD',
              ''.join(f'{entry},,\n' for entry in record))
    return importlib.metadata.Distribution.at(
        os.path.join(develop_eggs, dist_info))


class DistLocationsTest(unittest.TestCase):
    """Unit tests for ``_dist_locations`` and its helpers.

    Develop eggs installed by zc.buildout >= 6 are PEP 660 editable
    installs whose dist-info lives in ``develop-eggs/``, so the test
    paths must come from the ``__editable__*.pth`` file (or the project
    root recorded in ``direct_url.json``) instead of ``locate_file('')``.
    See https://github.com/zopefoundation/zc.recipe.testrunner/issues/26
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='dist-locations')
        self.develop_eggs = os.path.join(self.tmp, 'develop-eggs')
        self.project = os.path.join(self.tmp, 'project')
        self.src = os.path.join(self.project, 'src')
        mkdir(self.project)
        mkdir(self.src)
        self.editable_direct_url = {
            'dir_info': {'editable': True},
            'url': 'file://' + self.project,
        }

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def locations(self, **kw):
        dist = make_dist_info(self.tmp, **kw)
        return zc.recipe.testrunner._dist_locations(dist)

    def test_no_direct_url_uses_dist_dir(self):
        # buildout <= 5 egg-link layout: no direct_url.json, the dist-info
        # parent (here develop-eggs) is the location, unchanged behavior.
        self.assertEqual(self.locations(), [self.develop_eggs])

    def test_corrupt_direct_url_json_is_ignored(self):
        self.assertEqual(self.locations(direct_url='{not json'),
                         [self.develop_eggs])

    def test_non_editable_direct_url_is_ignored(self):
        self.assertEqual(
            self.locations(direct_url={'url': 'file:///x',
                                       'archive_info': {}}),
            [self.develop_eggs])
        self.assertEqual(
            self.locations(name='pkg2',
                           direct_url={'dir_info': {'editable': False},
                                       'url': 'file:///x'}),
            [self.develop_eggs])

    def test_non_file_url_is_ignored(self):
        self.assertEqual(
            self.locations(direct_url={'dir_info': {'editable': True},
                                       'url': 'https://example.com/pkg'}),
            [self.develop_eggs])
        self.assertEqual(
            self.locations(name='pkg2',
                           direct_url={'dir_info': {'editable': True}}),
            [self.develop_eggs])

    def test_static_pth_single_line(self):
        self.assertEqual(
            self.locations(direct_url=self.editable_direct_url,
                           pth_lines=[self.src]),
            [self.src])

    def test_static_pth_multiple_lines(self):
        self.assertEqual(
            self.locations(direct_url=self.editable_direct_url,
                           pth_lines=[self.src, self.project]),
            [self.src, self.project])

    def test_pth_filters_blank_comment_and_import_lines(self):
        self.assertEqual(
            self.locations(direct_url=self.editable_direct_url,
                           pth_lines=['', '# comment',
                                      'import foo; foo.install()',
                                      self.src]),
            [self.src])

    def test_finder_style_pth_falls_back_to_project_root(self):
        self.assertEqual(
            self.locations(
                direct_url=self.editable_direct_url,
                pth_lines=['import __editable___pkg_1_0_finder; '
                           '__editable___pkg_1_0_finder.install()']),
            [self.project])

    def test_pth_missing_on_disk_falls_back_to_project_root(self):
        # Python >= 3.11 drops missing files from ``dist.files``; on
        # Python 3.10 the entry survives and opening it fails.  Either
        # way the project root is used.
        self.assertEqual(
            self.locations(direct_url=self.editable_direct_url,
                           record=['__editable__.pkg-1.0.pth']),
            [self.project])

    def test_unreadable_pth_falls_back_to_project_root(self):
        # A directory in place of the .pth file makes open() raise
        # OSError while the path still exists.
        mkdir(self.tmp, 'develop-eggs')
        mkdir(self.tmp, 'develop-eggs', '__editable__.pkg-1.0.pth')
        self.assertEqual(
            self.locations(direct_url=self.editable_direct_url,
                           record=['__editable__.pkg-1.0.pth']),
            [self.project])

    def test_no_record_falls_back_to_project_root(self):
        self.assertEqual(
            self.locations(direct_url=self.editable_direct_url,
                           record=False),
            [self.project])

    def test_record_without_pth_falls_back_to_project_root(self):
        self.assertEqual(
            self.locations(direct_url=self.editable_direct_url,
                           record=['pkg-1.0.dist-info/METADATA',
                                   '../../bin/test']),
            [self.project])

    def test_pth_name_is_not_restricted_to_setuptools_naming(self):
        # Other build backends name their .pth file differently, e.g.
        # hatchling writes ``_editable_impl_<name>.pth``.  The file is
        # found via RECORD, so the name does not matter.
        self.assertEqual(
            self.locations(direct_url=self.editable_direct_url,
                           pth_name='_editable_impl_pkg.pth',
                           pth_lines=[self.src]),
            [self.src])

    def test_relative_pth_line_resolved_against_develop_eggs(self):
        self.assertEqual(
            self.locations(direct_url=self.editable_direct_url,
                           pth_lines=['linktree']),
            [os.path.join(self.develop_eggs, 'linktree')])


SRC_LAYOUT_SETUP_PY = """\
from setuptools import setup
setup(
    name="srcpkg",
    package_dir={"": "src"},
    packages=["srcpkg"],
)
"""

SRC_LAYOUT_BUILDOUT_CFG = """\
[buildout]
develop = srcpkg
parts = testsrcpkg
offline = true

[testsrcpkg]
recipe = zc.recipe.testrunner
eggs = srcpkg
script = test
working-directory = sample_working_dir
"""


class SrcLayoutTest(unittest.TestCase):
    """The test paths of a develop egg must point at its source directory.

    With zc.buildout >= 6 (PEP 660 editable installs) the naive location
    of a develop egg is the ``develop-eggs`` directory, in which
    zope.testrunner finds no tests.  Both the egg-link layout
    (buildout <= 5) and the editable install layout (buildout >= 6) must
    yield ``--test-path`` values pointing at ``srcpkg/src``.
    """

    def setUp(self):
        self.location = os.getcwd()

        self.tmp = tempfile.mkdtemp(prefix='sample-buildout')
        write(self.tmp, 'buildout.cfg', SRC_LAYOUT_BUILDOUT_CFG)
        mkdir(self.tmp, 'sample_working_dir')
        mkdir(self.tmp, 'srcpkg')
        mkdir(self.tmp, 'srcpkg', 'src')
        mkdir(self.tmp, 'srcpkg', 'src', 'srcpkg')
        write(self.tmp, 'srcpkg', 'src', 'srcpkg', '__init__.py', '')
        write(self.tmp, 'srcpkg', 'src', 'srcpkg', 'tests.py', TESTS_PY)
        write(self.tmp, 'srcpkg', 'setup.py', SRC_LAYOUT_SETUP_PY)
        write(self.tmp, 'srcpkg', 'README.rst', '')

        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.location)
        shutil.rmtree(self.tmp)

    def runTest(self):
        zc.buildout.buildout.Buildout(
            'buildout.cfg',
            [('buildout', 'log-level', 'WARNING')]
        ).init('fake-argument')

        with open(os.path.join(self.tmp, 'bin', 'test')) as f:
            script = f.read()
        test_paths = re.findall(r"'--test-path', '([^']*)'", script)
        expected = os.path.join(self.tmp, 'srcpkg', 'src')
        self.assertEqual([os.path.realpath(p) for p in test_paths],
                         [os.path.realpath(expected)])

        output = system(
            os.path.join(self.tmp, 'bin', 'test') + ' --list-tests')
        self.assertIn('srcpkg.tests', output)


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('zc.recipe.testrunner', test)
    zc.buildout.testing.install_develop('zc.recipe.egg', test)
    zc.buildout.testing.install('zope.testing', test)
    zc.buildout.testing.install('zope.testrunner', test)
    zc.buildout.testing.install('zope.interface', test)
    zc.buildout.testing.install('zope.exceptions', test)


checker = zope.testing.renormalizing.RENormalizing([
    zc.buildout.testing.normalize_path,
    zc.buildout.testing.normalize_script,
    zc.buildout.testing.normalize_egg_py,
    zc.buildout.testing.normalize_endings,
    (re.compile(r'#!\S+py\S*'), '#!python'),
    (re.compile(r'\d[.]\d+ seconds'), '0.001 seconds'),
    (re.compile(r'\d[.]\d+ s'), '0.001 s'),
    (re.compile('zope.testing-[^-]+-'), 'zope.testing-X-'),
    (re.compile('zope.testrunner-[^-]+-'), 'zope.testrunner-X-'),
    (re.compile('setuptools-[^-]+-'), 'setuptools-X-'),
    (re.compile('distribute-[^-]+-'), 'setuptools-X-'),
    (re.compile('zope.interface-[^-]+-'), 'zope.interface-X-'),
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
    (re.compile(r'parts\\\\'), 'parts/'),
    # Ignore pkg_resources deprecation warnings:
    (re.compile(r'.*pkg_resources is deprecated as an API.*\n'), ''),
    (re.compile(
        r'.*from pkg_resources import PkgResourcesDeprecationWarning.*\n'),
        ''),
    # Ignore Setuptools deprecation warnings for now:
    (re.compile(r'.*EasyInstallDeprecationWarning.*\n'), ''),
    (re.compile(r'.*SetuptoolsDeprecationWarning.*\n'), ''),
    # Ignore warnings for Python <= 3.10:
    (re.compile(r'.*warnings.warn\(\n'), ''),
    # Ignore Setuptools warnings:
    (lambda s: s.replace('*' * 80, '')),
    (lambda s: s.replace('!!\n', '')),
    (lambda s: s.replace(
        'Please avoid running ``setup.py`` and ``easy_install``.', '')),
    (lambda s: s.replace(
        'Please avoid running ``setup.py`` directly.', '')),
    (lambda s: s.replace(
        'Instead, use pypa/build, pypa/installer or other', '')),
    (lambda s: s.replace('standards-based tools.', '')),
    (lambda s: s.replace(
        'See https://github.com/pypa/setuptools/issues/917 for details.', '')),
    (lambda s: s.replace(
        'See https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html'
        ' for details.', '')),
    (lambda s: s.replace('easy_install.initialize_options(self)', '')),
    (lambda s: s.replace('self.initialize_options()', '')),
    (lambda s: s.strip()),  # clean up leftovers from replacements
])


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'README.rst',
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            checker=checker,
            optionflags=doctest.ELLIPSIS,
        ),
        AbsPathTest(),
        ExtrasInEggsTest(),
        SrcLayoutTest(),
        unittest.defaultTestLoader.loadTestsFromTestCase(DistLocationsTest),
    ))
