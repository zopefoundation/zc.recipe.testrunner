import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


name = "zc.recipe.testrunner"
setup(
    name=name,
    version='2.1.dev0',
    author="Jim Fulton",
    author_email="jim@zope.com",
    description="ZC Buildout recipe for creating test runners",
    long_description=(
        read('README.txt')
        + '\n' +
        read('CHANGES.txt')
        + '\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('src', 'zc', 'recipe', 'testrunner', 'README.txt')
        ),
    license="ZPL 2.1",
    keywords="development build testing",
    url='https://github.com/zopefoundation/zc.recipe.testrunner',
    packages=find_packages('src'),
    include_package_data=True,
    package_dir={'': 'src'},
    namespace_packages=['zc', 'zc.recipe'],
    extras_require={
        'tests': ['zope.testing'],
    },
    install_requires=[
        'zc.buildout >= 1.2.0',
        'zope.testrunner',
        'setuptools',
        'zc.recipe.egg >= 1.2.0',
    ],
    tests_require=['zope.testing'],
    test_suite=name + '.tests.test_suite',
    entry_points={
        'zc.buildout': ['default = %s:TestRunner' % name],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Buildout",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
