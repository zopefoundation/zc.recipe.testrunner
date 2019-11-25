Test-Runner Recipe
==================

The test-runner recipe, zc.recipe.testrunner, creates a test runner
for a project.

The test-runner recipe has several options:

eggs
    The eggs option specified a list of eggs to test given as one ore
    more setuptools requirement strings.  Each string must be given on
    a separate line.

script
    The script option gives the name of the script to generate, in the
    buildout bin directory.  Of the option isn't used, the part name
    will be used.

extra-paths
    One or more extra paths to include in the generated test script.

defaults
    The defaults option lets you specify testrunner default
    options. These are specified as Python source for an expression
    yielding a list, typically a list literal.

working-directory
    The working-directory option lets to specify a directory where the
    tests will run. The testrunner will change to this directory when
    run. If the working directory is the empty string or not specified
    at all, the recipe will create a working directory among the parts.

environment
    A set of environment variables that should be exported before
    starting the tests.

initialization
    Provide initialization code to run before running tests.

relative-paths
    Use egg, test, and working-directory paths relative to the test script.

(Note that, at this time, due to limitations in the Zope test runner, the
distributions cannot be zip files. TODO: Fix the test runner!)

To illustrate this, we'll create a pair of projects in our sample
buildout:

    >>> mkdir(sample_buildout, 'demo')
    >>> mkdir(sample_buildout, 'demo', 'demo')
    >>> write(sample_buildout, 'demo', 'demo', '__init__.py', '')
    >>> write(sample_buildout, 'demo', 'demo', 'tests.py',
    ... '''
    ... import unittest
    ...
    ... class TestDemo(unittest.TestCase):
    ...    def test(self):
    ...        pass
    ...
    ... def test_suite():
    ...     return unittest.makeSuite(TestDemo)
    ... ''')

    >>> write(sample_buildout, 'demo', 'setup.py',
    ... """
    ... from setuptools import setup
    ...
    ... setup(name = "demo")
    ... """)

    >>> write(sample_buildout, 'demo', 'README.txt', '')

    >>> mkdir(sample_buildout, 'demo2')
    >>> mkdir(sample_buildout, 'demo2', 'demo2')
    >>> write(sample_buildout, 'demo2', 'demo2', '__init__.py', '')
    >>> write(sample_buildout, 'demo2', 'demo2', 'tests.py',
    ... '''
    ... import unittest
    ...
    ... class Demo2Tests(unittest.TestCase):
    ...    def test2(self):
    ...        pass
    ...
    ... def test_suite():
    ...     return unittest.makeSuite(Demo2Tests)
    ... ''')

    >>> write(sample_buildout, 'demo2', 'setup.py',
    ... """
    ... from setuptools import setup
    ...
    ... setup(name = "demo2", install_requires= ['demoneeded'])
    ... """)

    >>> write(sample_buildout, 'demo2', 'README.txt', '')

Demo 2 depends on demoneeded:

    >>> mkdir(sample_buildout, 'demoneeded')
    >>> mkdir(sample_buildout, 'demoneeded', 'demoneeded')
    >>> write(sample_buildout, 'demoneeded', 'demoneeded', '__init__.py', '')
    >>> write(sample_buildout, 'demoneeded', 'demoneeded', 'tests.py',
    ... '''
    ... import unittest
    ...
    ... class TestNeeded(unittest.TestCase):
    ...    def test_needed(self):
    ...        pass
    ...
    ... def test_suite():
    ...     return unittest.makeSuite(TestNeeded)
    ... ''')

    >>> write(sample_buildout, 'demoneeded', 'setup.py',
    ... """
    ... from setuptools import setup
    ...
    ... setup(name = "demoneeded")
    ... """)

    >>> write(sample_buildout, 'demoneeded', 'README.txt', '')

We'll update our buildout to install the demo project as a
develop egg and to create the test script:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... develop = demo demoneeded demo2
    ... parts = testdemo
    ... offline = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs =
    ...    demo
    ...    demo2
    ... script = test
    ... """)

Note that we specified both demo and demo2 in the eggs
option and that we put them on separate lines.

We also specified the offline option to run the buildout in offline mode.

Now when we run the buildout:

    >>> import os
    >>> os.chdir(sample_buildout)
    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

We get a test script installed in our bin directory:

    >>> ls(sample_buildout, 'bin')
    -  buildout
    -  test

We also get a part directory for the tests to run in:

    >>> ls(sample_buildout, 'parts')
    d  testdemo


And updating leaves its contents intact:

    >>> _ = system(os.path.join(sample_buildout, 'bin', 'test') +
    ...            ' -q --coverage=coverage')
    >>> ls(sample_buildout, 'parts', 'testdemo')
    d  coverage
    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')
    >>> ls(sample_buildout, 'parts', 'testdemo')
    d  coverage

We can run the test script to run our demo test:

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'test') + ' -vv'),
    ...        end='')
    Running tests at level 1
    Running zope.testrunner.layer.UnitTests tests:
      Set up zope.testrunner.layer.UnitTests in 0.001 seconds.
      Running:
     test (demo.tests.TestDemo)
     test2 (demo2.tests.Demo2Tests)
      Ran 2 tests with 0 failures, 0 errors and 0 skipped in 0.001 seconds.
    Tearing down left over layers:
      Tear down zope.testrunner.layer.UnitTests in 0.001 seconds.

Note that we didn't run the demoneeded tests.  Tests are only run for
the eggs listed, not for their dependencies.

If we leave the script option out of the configuration, then the test
script will get it's name from the part:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... develop = demo
    ... parts = testdemo
    ... offline = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs = demo
    ... """)

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

    >>> ls(sample_buildout, 'bin')
    -  buildout
    -  testdemo

We can run the test script to run our demo test:

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'testdemo') + ' -q'),
    ...        end='')
    Running zope.testrunner.layer.UnitTests tests:
      Set up zope.testrunner.layer.UnitTests in 0.001 seconds.
      Ran 1 tests with 0 failures, 0 errors and 0 skipped in 0.001 seconds.
    Tearing down left over layers:
      Tear down zope.testrunner.layer.UnitTests in 0.001 seconds.

If we need to include other paths in our test script, we can use the
extra-paths option to specify them:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... develop = demo
    ... parts = testdemo
    ... offline = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs = demo
    ... extra-paths = /usr/local/zope/lib/python
    ... """)

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

    >>> cat(sample_buildout, 'bin', 'testdemo')  # doctest: +ELLIPSIS
    #!/usr/local/bin/python2.4
    <BLANKLINE>
    import sys
    sys.path[0:0] = [
      ...
      ]
    <BLANKLINE>
    import os
    sys.argv[0] = os.path.abspath(sys.argv[0])
    os.chdir('/sample-buildout/parts/testdemo')
    <BLANKLINE>
    <BLANKLINE>
    import zope.testrunner
    <BLANKLINE>
    if __name__ == '__main__':
        sys.exit(zope.testrunner.run([
            '--test-path', '/sample-buildout/demo',
            ]))

We can use the working-directory option to specify a working
directory:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... develop = demo
    ... parts = testdemo
    ... offline = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs = demo
    ... extra-paths = /usr/local/zope/lib/python
    ... working-directory = /foo/bar
    ... """)

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

    >>> cat(sample_buildout, 'bin', 'testdemo')  # doctest: +ELLIPSIS
    #!/usr/local/bin/python2.4
    <BLANKLINE>
    import sys
    sys.path[0:0] = [
      ...
      ]
    <BLANKLINE>
    import os
    sys.argv[0] = os.path.abspath(sys.argv[0])
    os.chdir('/foo/bar')
    <BLANKLINE>
    <BLANKLINE>
    import zope.testrunner
    <BLANKLINE>
    if __name__ == '__main__':
        sys.exit(zope.testrunner.run([
            '--test-path', '/sample-buildout/demo',
            ]))

Now that out tests use a specified working directory, their designated
part directory is gone:

    >>> ls(sample_buildout, 'parts')

If we need to specify default options, we can use the defaults
option. For example, Zope 3 applications typically define test suites
in modules named ftests or tests.  The default test runner behaviour
is to look in modules named tests.  To specify that we want to look in
tests and ftests module, we'd supply a default for the --tests-pattern
option.  If we like dots, we could also request more verbose output
using the -v option:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... develop = demo
    ... parts = testdemo
    ... offline = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs = demo
    ... extra-paths = /usr/local/zope/lib/python
    ... defaults = ['--tests-pattern', '^f?tests$',
    ...             '-v'
    ...            ]
    ... """)

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

    >>> cat(sample_buildout, 'bin', 'testdemo')  # doctest: +ELLIPSIS
    #!/usr/local/bin/python2.4
    <BLANKLINE>
    import sys
    sys.path[0:0] = [
      ...
      ]
    <BLANKLINE>
    import os
    sys.argv[0] = os.path.abspath(sys.argv[0])
    os.chdir('/sample-buildout/parts/testdemo')
    <BLANKLINE>
    <BLANKLINE>
    import zope.testrunner
    <BLANKLINE>
    if __name__ == '__main__':
        sys.exit(zope.testrunner.run((['--tests-pattern', '^f?tests$',
    '-v'
    ]) + [
            '--test-path', '/sample-buildout/demo',
            ]))

Some things to note from this example:

- Parentheses are placed around the given expression.

- Leading whitespace is removed.


To demonstrate the ``environment`` option, we first update the tests to
include a check for an environment variable:

    >>> write(sample_buildout, 'demo', 'demo', 'tests.py',
    ... '''
    ... import unittest
    ... import os
    ...
    ... class DemoTests(unittest.TestCase):
    ...    def test(self):
    ...        self.assertEqual('42', os.environ.get('zc.recipe.testrunner', '23'))
    ...
    ... def test_suite():
    ...     return unittest.makeSuite(DemoTests)
    ... ''')

Running them with the current buildout will produce a failure:

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'testdemo')
    ...               + ' -vv'),
    ...        end='') # doctest: +ELLIPSIS
    Running tests at level 1
    Running zope.testrunner.layer.UnitTests tests:
      Set up zope.testrunner.layer.UnitTests in 0.001 seconds.
      Running:
     test (demo.tests.DemoTests) (... s)
    <BLANKLINE>
    <BLANKLINE>
    Failure in test test (demo.tests.DemoTests)
    Traceback (most recent call last):
      ...
    AssertionError: '42' != '23'
    ...
      Ran 1 tests with 1 failures, 0 errors and 0 skipped in 0.001 seconds.
    Tearing down left over layers:
      Tear down zope.testrunner.layer.UnitTests in 0.001 seconds.
    <BLANKLINE>
    Tests with failures:
       test (demo.tests.DemoTests)


Let's update the buildout to specify the environment variable for the test
runner:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... develop = demo
    ... parts = testdemo
    ... offline = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs = demo
    ... environment = testenv
    ...
    ... [testenv]
    ... zc.recipe.testrunner = 42
    ... """)

We run buildout and see that the test runner script now includes setting up
the environment variable. Also, the tests pass again:

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

    >>> cat(sample_buildout, 'bin', 'testdemo')  # doctest: +ELLIPSIS
    #!/usr/local/bin/python2.4
    <BLANKLINE>
    import sys
    sys.path[0:0] = [
      ...
      ]
    <BLANKLINE>
    import os
    sys.argv[0] = os.path.abspath(sys.argv[0])
    os.chdir('/sample-buildout/parts/testdemo')
    os.environ['zc.recipe.testrunner'] = '42'
    <BLANKLINE>
    <BLANKLINE>
    import zope.testrunner
    <BLANKLINE>
    if __name__ == '__main__':
        sys.exit(zope.testrunner.run([
            '--test-path', '/sample-buildout/demo',
            ]))

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'testdemo')+' -vv'),
    ...        end='')
    Running tests at level 1
    Running zope.testrunner.layer.UnitTests tests:
      Set up zope.testrunner.layer.UnitTests in 0.001 seconds.
      Running:
     test (demo.tests.DemoTests)
      Ran 1 tests with 0 failures, 0 errors and 0 skipped in 0.001 seconds.
    Tearing down left over layers:
      Tear down zope.testrunner.layer.UnitTests in 0.001 seconds.

One can add initialization steps in the buildout.  These will be added to the
end of the script:

    >>> write(sample_buildout, 'buildout.cfg',
    ... r"""
    ... [buildout]
    ... develop = demo
    ... parts = testdemo
    ... offline = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs = demo
    ... extra-paths = /usr/local/zope/lib/python
    ... defaults = ['--tests-pattern', '^f?tests$',
    ...             '-v'
    ...            ]
    ... initialization = sys.stdout.write('Hello all you egg-laying pythons!\n')
    ... """)

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

    >>> cat(sample_buildout, 'bin', 'testdemo')  # doctest: +ELLIPSIS
    #!/usr/local/bin/python2.4
    <BLANKLINE>
    import sys
    sys.path[0:0] = [
      ...
      ]
    <BLANKLINE>
    import os
    sys.argv[0] = os.path.abspath(sys.argv[0])
    os.chdir('/sample-buildout/parts/testdemo')
    sys.stdout.write('Hello all you egg-laying pythons!\n')
    <BLANKLINE>
    import zope.testrunner
    <BLANKLINE>
    if __name__ == '__main__':
        sys.exit(zope.testrunner.run((['--tests-pattern', '^f?tests$',
    '-v'
    ]) + [
            '--test-path', '/sample-buildout/demo',
            ]))

This will also work with a multi-line initialization section:

    >>> write(sample_buildout, 'buildout.cfg',
    ... r"""
    ... [buildout]
    ... develop = demo
    ... parts = testdemo
    ... offline = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs = demo
    ... extra-paths = /usr/local/zope/lib/python
    ... defaults = ['--tests-pattern', '^f?tests$',
    ...             '-v'
    ...            ]
    ... initialization = sys.stdout.write('Hello all you egg-laying pythons!\n')
    ...               sys.stdout.write('I thought pythons were live bearers?\n')
    ... """)

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

    >>> cat(sample_buildout, 'bin', 'testdemo')  # doctest: +ELLIPSIS
    #!/usr/local/bin/python2.4
    <BLANKLINE>
    import sys
    sys.path[0:0] = [
      ...
      ]
    <BLANKLINE>
    import os
    sys.argv[0] = os.path.abspath(sys.argv[0])
    os.chdir('/sample-buildout/parts/testdemo')
    sys.stdout.write('Hello all you egg-laying pythons!\n')
    sys.stdout.write('I thought pythons were live bearers?\n')
    <BLANKLINE>
    import zope.testrunner
    <BLANKLINE>
    if __name__ == '__main__':
        sys.exit(zope.testrunner.run((['--tests-pattern', '^f?tests$',
    '-v'
    ]) + [
            '--test-path', '/sample-buildout/demo',
            ]))

If the relative-paths option is used, egg (and extra) paths are
generated relative to the test script.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... develop = demo
    ... parts = testdemo
    ... offline = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs = demo
    ... extra-paths = /usr/local/zope/lib/python
    ...               ${buildout:directory}/sources
    ... relative-paths = true
    ... """)

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

    >>> cat(sample_buildout, 'bin', 'testdemo')  # doctest: +ELLIPSIS
    #!/usr/local/bin/python2.4
    <BLANKLINE>
    import os
    <BLANKLINE>
    join = os.path.join
    base = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
    base = os.path.dirname(base)
    <BLANKLINE>
    import sys
    sys.path[0:0] = [
      join(base, 'demo'),
      ...
      '/usr/local/zope/lib/python',
      join(base, 'sources'),
      ]
    <BLANKLINE>
    import os
    sys.argv[0] = os.path.abspath(sys.argv[0])
    os.chdir(join(base, 'parts/testdemo'))
    <BLANKLINE>
    <BLANKLINE>
    import zope.testrunner
    <BLANKLINE>
    if __name__ == '__main__':
        sys.exit(zope.testrunner.run([
            '--test-path', join(base, 'demo'),
            ]))

The relative-paths option can be specified at the buildout level:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... develop = demo
    ... parts = testdemo
    ... offline = true
    ... relative-paths = true
    ...
    ... [testdemo]
    ... recipe = zc.recipe.testrunner
    ... eggs = demo
    ... extra-paths = /usr/local/zope/lib/python
    ...               ${buildout:directory}/sources
    ... """)

    >>> print_(system(os.path.join(sample_buildout, 'bin', 'buildout') + ' -q'),
    ...        end='')

    >>> cat(sample_buildout, 'bin', 'testdemo')  # doctest: +ELLIPSIS
    #!/usr/local/bin/python2.4
    <BLANKLINE>
    import os
    <BLANKLINE>
    join = os.path.join
    base = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
    base = os.path.dirname(base)
    <BLANKLINE>
    import sys
    sys.path[0:0] = [
      join(base, 'demo'),
      ...
      '/usr/local/zope/lib/python',
      join(base, 'sources'),
      ]
    <BLANKLINE>
    import os
    sys.argv[0] = os.path.abspath(sys.argv[0])
    os.chdir(join(base, 'parts/testdemo'))
    <BLANKLINE>
    <BLANKLINE>
    import zope.testrunner
    <BLANKLINE>
    if __name__ == '__main__':
        sys.exit(zope.testrunner.run([
            '--test-path', join(base, 'demo'),
            ]))

