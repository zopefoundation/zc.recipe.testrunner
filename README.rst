******************
Test-Runner Recipe
******************

.. contents::

This recipe generates zope.testing test-runner scripts for testing a
collection of eggs.

Example usage in ``buildout.cfg``::

    [buildout]
    parts = test

    [test]
    recipe = zc.recipe.testrunner
    eggs = <eggs to test>
