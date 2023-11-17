# Copyright (c) Quectel Wireless Solution, Co., Ltd.All Rights Reserved.
#  
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  
#     http://www.apache.org/licenses/LICENSE-2.0
#  
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages

VERSION = "0.2.0"


def readme():
    with open('README.rst', encoding='utf-8') as f:
        content = f.read()
    return content


def get_version():
    return VERSION


setup(
    name='thonny-quecpython',
    version=get_version(),
    description='quecpython programing kits for thonny',
    long_description=readme(),
    long_description_content_type='text/x-rst',
    python_requires='>=3.7',
    license="MIT License",
    author='dustin.wei',
    author_email='dustin.wei@quectel.com',
    keywords=["QuecPython", "quecpython", "QuecPython Kits", "quecpython kits"],
    url='https://github.com/QuecPython/thonny-quecpython',
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
            "exes/Eigen/*",
            "exes/Eigen/image_ec618/*",
            "exes/Eigen/image_ec618/agentboot_uart/*",
            "exes/Eigen/image_ec618/agentboot_usb/*",
            "exes/Eigen/image_ec618/pkgdir/*",
            "exes/Eigen/image_ec618/pkgdir/pkg_extract_tmp/*",
        ],
        "thonnycontrib.quecpython.locale": [
            "zh_CN.lag",
        ],
        "thonnycontrib.quecpython.backend": [
            "base_api_stubs/*",
            "generic_api_stubs/*",
        ]
    },
    install_requires=[
        'thonny>=4.1.1',
        'Pypubsub>=4.0.3'
    ],
)
