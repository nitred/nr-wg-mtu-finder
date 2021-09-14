import re
from codecs import open  # To use a consistent encoding
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


# Get version without importing, which avoids dependency issues
def get_version():
    with open("nr_wg_mtu_finder/__init__.py") as version_file:
        return re.search(
            r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""", version_file.read()
        ).group("version")


install_requires = [
    "pandas>=0.23.4",
    "matplotlib",
    "seaborn",
    "pydantic",
    "requests",
    "flask",
]


setup(
    name="nr-wg-mtu-finder",
    description="Scripts to find the optimal MTU for Wireguard server and peers.",
    long_description=long_description,
    version=get_version(),
    include_package_data=True,
    install_requires=install_requires,
    setup_requires=["pytest-runner"],
    entry_points="""
        [console_scripts]
        nr-wg-mtu-finder=nr_wg_mtu_finder.main:run
    """,
    packages=find_packages(),
    zip_safe=False,
    author="Nitish K Reddy",
    author_email="nitish.k.reddy@gmail.com",
    # download_url="github.com/nitred/nr-wg-mtu-finder/archive/{}.tar.gz".format(get_version()),
    classifiers=["Programming Language :: Python :: 3.7"],
)
