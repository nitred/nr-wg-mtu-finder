import re
from codecs import open  # To use a consistent encoding
from os import path

from setuptools import find_packages, setup

# Get version without importing, which avoids dependency issues
def get_version():
    with open("nr_wg_mtu_finder/__init__.py") as version_file:
        return re.search(
            r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""", version_file.read()
        ).group("version")


install_requires = [
    "pandas>=0.23.4,<1.4",
    "matplotlib<3.5",
    "seaborn<0.12",
    "pydantic<1.9",
    "requests<2.28",
    "flask<2.1",
]


setup(
    name="nr-wg-mtu-finder",
    description="Scripts to find the optimal MTU for Wireguard server and peers.",
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
