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

# See pyproject.toml for package metadata
setup()
