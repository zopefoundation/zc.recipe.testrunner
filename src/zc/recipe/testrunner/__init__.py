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
"""A few built-in recipes

$Id$
"""

import importlib.metadata
import json
import os
import os.path
import sys
from urllib.parse import urlparse
from urllib.request import url2pathname

import zc.buildout.easy_install
import zc.recipe.egg
from packaging.requirements import Requirement as PackagingRequirement
from packaging.utils import canonicalize_name


class TestRunner:

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        options['script'] = os.path.join(buildout['buildout']['bin-directory'],
                                         options.get('script', self.name),
                                         )
        if not options.get('working-directory', ''):
            options['location'] = os.path.join(
                buildout['buildout']['parts-directory'], name)
        self.egg = zc.recipe.egg.Egg(buildout, name, options)

    def install(self):
        options = self.options
        dest = []
        eggs, ws = self.egg.working_set(('zope.testrunner', ))

        dist_map = {}
        for d in importlib.metadata.distributions(path=list(ws.entries)):
            name = d.metadata.get('Name')
            if name:  # pragma: no branch
                dist_map.setdefault(canonicalize_name(name),
                                    _dist_locations(d))

        test_paths = []
        for spec in eggs:
            name = PackagingRequirement(spec).name
            locations = dist_map.get(canonicalize_name(name))
            if locations is None:  # pragma: no cover
                raise ValueError(
                    f"Requirement not found in working set: {spec}")
            test_paths.extend(locations)

        # The test paths must be importable in the generated script.  With
        # buildout <= 5 they always are (each is a working set entry), but
        # for a PEP 660 editable install (zc.buildout >= 6) whose source
        # directory is only reachable through an import hook this is not
        # guaranteed.  zc.buildout.easy_install.scripts() removes
        # duplicates, so already importable paths are not repeated.
        extra_paths = self.egg.extra_paths + test_paths

        defaults = options.get('defaults', '').strip()
        if defaults:
            defaults = '(%s) + ' % defaults

        wd = options.get('working-directory', '')
        if not wd:
            wd = options['location']
            if os.path.exists(wd):
                assert os.path.isdir(wd)
            else:
                os.mkdir(wd)
            dest.append(wd)
        wd = os.path.abspath(wd)

        if self.egg._relative_paths:
            wd = _relativize(self.egg._relative_paths, wd)
            test_paths = [_relativize(self.egg._relative_paths, p)
                          for p in test_paths]
        else:
            wd = repr(wd)
            test_paths = map(repr, test_paths)

        initialization = initialization_template % wd

        env_section = options.get('environment', '').strip()
        if env_section:
            env = self.buildout[env_section]
            for key, value in env.items():
                initialization += env_template % (key, value)

        initialization_section = options.get('initialization', '').strip()
        if initialization_section:
            initialization += initialization_section

        dest.extend(zc.buildout.easy_install.scripts(
            [(options['script'], 'zope.testrunner', 'run')],
            ws, options['executable'],
            self.buildout['buildout']['bin-directory'],
            extra_paths=extra_paths,
            arguments=defaults + (
                '[\n' +
                ''.join(("        '--test-path', %s,\n" % p)
                        for p in test_paths)
                + '        ]'),
            initialization=initialization,
            relative_paths=self.egg._relative_paths,
        ))

        return dest

    update = install


arg_template = """\
['--test-path', %(TESTPATH)s,]
"""

initialization_template = """\
import os
sys.argv[0] = os.path.abspath(sys.argv[0])
os.chdir(%s)
"""

env_template = """\
os.environ['%s'] = %r
"""


def _editable_project_root(dist):
    """Project root of a PEP 660 editable install, or None if not editable."""
    text = dist.read_text('direct_url.json')
    if text is None:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    if not data.get('dir_info', {}).get('editable'):
        return None
    url = urlparse(data.get('url', ''))
    if url.scheme != 'file':
        return None
    return url2pathname(url.path)


def _pth_paths(dist):
    """Source paths from the ``.pth`` file(s) installed by the dist.

    The ``.pth`` files are found via the distribution's ``RECORD``, so
    any name works: setuptools writes ``__editable__*.pth``, hatchling
    ``_editable_impl_*.pth``, other backends use yet other names.
    Mirrors the line filtering of ``zc.buildout.utils.get_pth_paths``;
    relative lines resolve against the ``.pth`` file's own directory.
    """
    paths = []
    for entry in dist.files or ():
        name = os.path.basename(str(entry))
        if not name.endswith('.pth'):
            continue
        pth = str(dist.locate_file(entry))
        try:
            with open(pth) as f:
                lines = f.read().splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('import '):
                continue
            paths.append(
                os.path.abspath(os.path.join(os.path.dirname(pth), line)))
    return paths


def _dist_locations(dist):
    """Directories containing the code of ``dist``, for use as test paths.

    For a PEP 660 editable install (a develop egg with zc.buildout >= 6)
    the ``.dist-info`` lives in ``develop-eggs/``, so ``locate_file('')``
    would point there instead of at the source directory.
    """
    root = _editable_project_root(dist)
    if root is not None:
        return _pth_paths(dist) or [root]
    return [str(dist.locate_file(''))]


def _relativize(base, path):
    base += os.path.sep
    if sys.platform == 'win32':  # pragma: no cover
        # windoze paths are case insensitive, but startswith is not
        base = base.lower()
        path = path.lower()

    if path.startswith(base):
        path = 'join(base, %r)' % path[len(base):]
    else:
        path = repr(path)  # pragma: no cover
    return path
