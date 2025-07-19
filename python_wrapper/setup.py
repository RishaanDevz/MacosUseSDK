 #!/usr/bin/env python3
"""
Setup script for MacosUseSDK Python wrapper
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Python wrapper for MacosUseSDK - macOS automation library"

setup(
    name="macos-use-sdk",
    version="1.0.0",
    author="MacosUseSDK Team",
    author_email="",
    description="Python wrapper for MacosUseSDK - macOS automation and accessibility library",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/MacosUseSDK",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Desktop Environment :: Gnome",
        "Topic :: System :: Operating System",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typing-extensions>=4.0.0; python_version<'3.11'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "macos-use-sdk=macos_use_sdk.cli:cli_main",
        ],
    },
    include_package_data=True,
    package_data={
        "macos_use_sdk": ["py.typed"],
    },
) 