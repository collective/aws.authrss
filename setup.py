"""aws.authrss packaging utility"""

from setuptools import setup

import os


def read(*names):
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, *names)
    return open(path).read().strip()


version = "3.0.0.dev0"

long_description = "\n\n".join(
    [
        open("README.md").read(),
        open("CONTRIBUTORS.md").read(),
        open("CHANGES.md").read(),
    ]
)

setup(
    name="aws.authrss",
    version=version,
    description="Private Plone RSS feeds through a user private token",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 6.2",
        "Natural Language :: English",
        "Natural Language :: French",
        "Natural Language :: German",
    ],
    keywords="plone rss",
    author="Gilles Lenfant",
    author_email="gilles.lenfant@alterway.fr",
    url="http://pypi.python.org/pypi/aws.authrss",
    project_urls={
        "PyPI": "https://pypi.org/project/aws.authrss/",
        "Source": "https://github.com/collective/aws.authrss",
        "Tracker": "https://github.com/collective/aws.authrss/issues",
    },
    license="GPL",
    python_requires=">3.10",
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Products.GenericSetup",
        "Zope",
        "plone.app.layout",
        "plone.base",
        "plone.protect",
        "plone.uuid",
    ],
    extras_require={
        "test": [
            "plone.api",
            "plone.browserlayer",
            "lxml",
            "Products.CMFCore",
            "plone.app.testing",
            "plone.testing>=5.0.0",
        ]
    },
    entry_points="""
    [plone.autoinclude.plugin]
    target = plone
    """,
)
