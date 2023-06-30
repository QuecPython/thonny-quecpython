from setuptools import setup, find_packages


def readme():
    with open('README.md', encoding='utf-8') as f:
        content = f.read()
    return content


setup(
    name='thonny-quecpython',
    version='0.1.0',
    description='quecpython programing kits',
    long_description=readme(),
    long_description_content_type='text/markdown',
    python_requires='>=3.7',
    license="MIT License",
    author='dustin.wei',
    author_email='dustin.wei@quectel.com',
    keywords=["QuecPython", "quecpython", "QuecPython Kits", "quecpython kits"],
    url='http://github.com/quecpython',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    platforms=["windows"],
    packages=find_packages(),
    package_data={
        "thonnycontrib.quecpython.fw": [
            "fw_config.json",
            "exes/aboot/*",
            "exes/blf_tools/*",
            "exes/NB/*",
            "exes/rda/*",
        ],
    },
    install_requires=[
        'thonny>=4.1.1',
        'Pypubsub>=4.0.3'
    ],
)
