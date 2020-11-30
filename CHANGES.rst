
Change History
**************

2.2 (2020-11-30)
================

- Add support for Python 3.9, PyPy2 and PyPy3.


2.1 (2019-05-14)
================

- Add support for Python 3.5 up to 3.8a3.


2.0.0 (2013-02-10)
==================

Work with buildout 2.

This was accomplised by starting from 1.3.0 then:

- Merge fixes from 1.2.1
  (svn://svn.zope.org/repos/main/zc.recipe.testrunner/tags/1.2.1)
  Excluding nailing zope.testing version. That fixes a bunch of
  windows issues

1.4.0 (2010-08-27)
==================

- Update to using zc.buildout 1.5.0 script generation.  This adds the
  following options: include-site-packages, allowed-eggs-from-site-packages,
  extends, and exec-sitecustomize.

- Merge fixes from 1.2.1
  (svn://svn.zope.org/repos/main/zc.recipe.testrunner/tags/1.2.1)
  Excluding nailing zope.testing version. That fixes a bunch of
  windows issues

1.3.0 (2010-06-09)
==================

- Updated tests to run with the last versions of all modules.

- Removed the usage of the deprecated zope.testing.doctest, therby also
  dropping Python 2.3 support.

- Started using zope.testrunner instead of zope.testing.testrunner.

1.2.1 (2010-08-24)
==================

- Fixed a lot of windows issues
- Nailed versions to ZTK 1.0a2 (oh well, we have to have at least some stability)
- Fixed some other test failures that seemed to come from other packages

1.2.0 (2009-03-23)
==================

- Added a relative-paths option to use egg, test, and
  working-directory paths relative to the test script.


1.1.0 (2008-08-25)
==================

- Requiring at least zope.testing 3.6.0.

- Fixed a bug: Parallel runs of layers failed when using
  working-directory parameter.


1.0.0 (2007-11-04)
==================

- Preparing stable release.


1.0.0b8 (2007-07-17)
====================

- Added the ability to use `initialization` option that will be inserted into
  the bin/test after the environment is set up.

1.0.0b7 (2007-04-26)
====================

Feature Changes
---------------

- Added optional option `environment` that allows defining a section in your
  buildout.cfg to specify environment variables that should be set before
  running the tests.

1.0.0b6 (2007-02-25)
====================

Feature Changes
---------------

- If the working directory is not specified, or specified as the empty
  string, an empty part directory is created for the tests to run in.

1.0.0b5 (2007-01-24)
====================

Bugs fixed
----------

- When:

  + the working-directory option was used,
  + and the test runner needed to restart itself
  + and the test runner was run with a relative path (e.g. bin/test)

  then the testrunner could not restart itself successfully because the
  relative path in sys.argv[0] was no-longer valid.

  Now we convert sys.argv[0] to an absolute path.

1.0.0b4 (2006-10-24)
====================

Feature Changes
---------------

- Added a working-directoy option to specify a working directory for
  the generated script.


1.0.0b3 (2006-10-16)
====================

Updated to work with (not get a warning from) zc.buildout 1.0.0b10.

1.0.0b2
=======

Added a defaults option to specify testrunner default options.

1.0.0b1
=======

Updated to work with zc.buildout 1.0.0b5.

1.0.0a3
=======

Added a defaults option that lets you specify test-runner default
options.


1.0.0a2
=======

Now provide a extra-paths option for including extra paths in test
scripts. This is useful when eggs depend on Python packages not
packaged as eggs.


1.0.0a1
=======

Initial public version
