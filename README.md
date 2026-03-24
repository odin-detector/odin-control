# odin-control

[![Test odin-control](https://github.com/odin-detector/odin-control/actions/workflows/test_odin_control.yml/badge.svg)](https://github.com/odin-detector/odin-control/actions/workflows/test_odin_control.yml)
[![codecov](https://codecov.io/gh/odin-detector/odin-control/branch/master/graph/badge.svg?token=Urucx8wsTU)](https://codecov.io/gh/odin-detector/odin-control)
[![PyPI](https://img.shields.io/pypi/v/odin-control.svg)](https://pypi.org/project/odin-control)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

Source          | <https://github.com/odin-detector/odin-control>
:---:           | :---:
PyPI            | `pip install odin-control`
Documentation   | <https://odin-detector.github.io/odin-control/>
Releases        | <https://github.com/odin-detector/odin-control/releases>

odin-control is a Python web application framework designed to support integration of the control
plane of scientific detector systems. Based on the [Tornado](https://tornadoweb.org) framework,
odin-control provides a REST-like API interface to a set of dynamically-loaded plugins, known as
*adapters*, which control the underlying detector system.
