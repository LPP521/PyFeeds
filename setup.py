from setuptools import find_packages, setup

setup(
    name="feeds",
    version="2017.08.14",
    # Author details
    author="Florian Preinstorfer, Lukas Anzinger",
    author_email="florian@nblock.org, lukas@lukasanzinger.at",
    url="https://github.com/nblock/feeds",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click>=6.6",
        "Scrapy>=1.1",
        "bleach>=1.4.3",
        "dateparser>=0.5.1",
        "feedparser",
        "lxml>=3.5.0",
        "python-dateutil>=2.7.3",
        "pyxdg>=0.26",
        "readability-lxml>=0.7",
    ],
    extras_require={
        "docs": ["doc8", "restructuredtext_lint", "sphinx", "sphinx_rtd_theme"],
        "style": ["black", "flake8", "isort"],
    },
    entry_points="""
        [console_scripts]
        feeds=feeds.cli:main
    """,
)
