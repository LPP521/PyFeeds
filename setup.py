from setuptools import setup, find_packages

setup(
    name='feeds',
    version='0.1-dev',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'bleach>=1.4.3',
        'Click>=6.6',
        'dateparser>=0.5.1',
        'Delorean>=0.6.0',
        'Scrapy>=1.1',
        'lxml>=3.5.0',
    ],
    extras_require={
        'doc': [
            'doc8',
            'restructuredtext_lint',
            'sphinx',
        ],
    },
    entry_points='''
        [console_scripts]
        feeds=feeds.cli:main
    ''',
)
