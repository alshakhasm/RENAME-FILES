#!/usr/bin/env python3
"""
Setup script for Date Prefix File Renamer
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="date-prefix-renamer",
    version="1.0.0",
    description="Desktop application that renames files and folders by adding creation date prefixes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Date Prefix Renamer Team",
    author_email="team@example.com",
    url="https://github.com/example/date-prefix-renamer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "tkinterdnd2>=0.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-mock>=3.10.0", 
            "pytest-cov>=4.0.0",
        ],
        "docker": [
            "docker>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "date-prefix-renamer=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment :: File Managers",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    keywords="file renaming, date prefix, filesystem, gui, desktop",
    project_urls={
        "Bug Reports": "https://github.com/example/date-prefix-renamer/issues",
        "Source": "https://github.com/example/date-prefix-renamer",
        "Documentation": "https://github.com/example/date-prefix-renamer/blob/main/README.md",
    },
)