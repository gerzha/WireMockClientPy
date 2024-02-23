from os import environ
from pathlib import Path

from setuptools import find_packages, setup

URL = "https://stash.wargaming.net/projects/MOBILE_PLATFORM/repos/qawiremock"
here: Path = Path(__file__).parent.absolute()
readme_filename = "HISTORY.md"
requirements_file = "requirements/requirements.txt"
requirements_file_quality = "requirements/requirements.quality.txt"

FILE_NAME = "VERSION"
version = None

if environ.get("CI_COMMIT_TAG"):
    version = environ["CI_COMMIT_TAG"]
elif environ.get("CI_PIPELINE_IID"):
    job_id = environ["CI_PIPELINE_IID"]
    with open(FILE_NAME) as file:
        current_version = file.read().strip()
    version = f"{current_version}.{job_id}"

if not version:
    with open(FILE_NAME) as file:
        version = file.read()
else:
    with open(FILE_NAME, "w") as file:
        file.write(version)


def get_readme() -> str:
    """get_readme.

    Extract long description from file.
    :return str: Package long description.
    """
    return (here / readme_filename).read_text()


def get_requirements(filename: str) -> list[str]:
    """get_requirements.

    Extract requirements form file.
    :return: List of requirements.
    """

    with (here / filename).open() as f:
        return [
            line
            for line in map(str.strip, f.readlines())
            if line and not line[0] in ("#", "-")
        ]


setup(
    name="qawiremock",
    description='The wiremock client for the functional testing of the "Game Grids" services.',  # noqa
    long_description=get_readme(),
    version=version,
    url=URL,
    author="Game Grids",
    platform="POSIX",
    packages=find_packages(),
    include_package_data=True,
    install_requires=get_requirements(filename=requirements_file),
    extras_require={"quality": get_requirements(filename=requirements_file_quality)},
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
)
