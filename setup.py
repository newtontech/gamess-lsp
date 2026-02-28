from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gamess-lsp",
    version="0.1.0",
    author="newtontech",
    author_email="",
    description="Language Server Protocol implementation for GAMESS (US)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/newtontech/gamess-lsp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pygls>=1.1.0",
        "lsprotocol>=2023.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gamess-lsp=gamess_lsp.cli:main",
        ],
    },
)
