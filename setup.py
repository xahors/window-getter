from setuptools import setup, find_packages

setup(
    name="window-getter",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "window-getter=window_getter.cli:main",
        ],
    },
)
