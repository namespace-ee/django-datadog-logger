#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()

requirements = []
with open("requirements.txt") as requirements_file:
    for line in requirements_file.readlines():
        # skip to next iteration if comment or empty line
        if line.startswith("#") or line == "" or line.startswith("http") or line.startswith("git"):
            continue
        # add line to requirements
        requirements.append(line)

setup_requirements = []

test_requirements = []


setup(
    author="Lenno Nagel",
    author_email="lenno@namespace.ee",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    description="Django DataDog Logger integration package.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="django_datadog_logger",
    name="django-datadog-logger",
    packages=find_packages(include=["django_datadog_logger", "django_datadog_logger.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/namespace-ee/django-datadog-logger",
    version="0.7.0",
    zip_safe=False,
)
