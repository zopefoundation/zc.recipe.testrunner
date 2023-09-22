******************
Test-Runner Recipe
******************

.. image:: https://github.com/zopefoundation/zc.recipe.testrunner/actions/workflows/tests.yml/badge.svg
        :target: https://github.com/zopefoundation/zc.recipe.testrunner/actions/workflows/tests.yml

.. image:: https://coveralls.io/repos/github/zopefoundation/zc.recipe.testrunner/badge.svg?branch=master
        :target: https://coveralls.io/github/zopefoundation/zc.recipe.testrunner?branch=master

.. image:: https://img.shields.io/pypi/v/zc.recipe.testrunner.svg
        :target: https://pypi.org/project/zc.recipe.testrunner/
        :alt: Current version on PyPI

.. image:: https://img.shields.io/pypi/pyversions/zc.recipe.testrunner.svg
        :target: https://pypi.org/project/zc.recipe.testrunner/
        :alt: Supported Python versions

.. contents::

This recipe generates zope.testing test-runner scripts for testing a
collection of eggs.

Example usage in ``buildout.cfg``::

    [buildout]
    parts = test

    [test]
    recipe = zc.recipe.testrunner
    eggs = <eggs to test>
