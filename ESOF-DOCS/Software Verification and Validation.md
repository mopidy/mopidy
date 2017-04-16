# Mopidy Software Verification and Validation

## Table of contents
@@TOC@@


## Introduction
Verifying a piece of software is to ensure that both the intermediate as well as the final product conform to their specification and requirements.
On the other hand, to validate software is to make sure that the final product will fulfull its intended environment, mainly through the use of tests.

The main techniques used for verifying and validating (V&V) are **static techniques** and **dynamic techniques**:

- **Static techniques**: analyze the static system representations to both find problems/bugs and evaluate quality. This includes reviews, inspections, formal verification, etc.
- **Dynamic techniques**: execute the system and observe its behavior (software testing and simulation).


In Mopidy the software is constantly and consistently validated through the use of tools such as [Travis CI](https://travis-ci.org) and [Tox](https://tox.readthedocs.org/en/latest/) with [pytest](http://pytest.org/latest/) as a backend for testing the python code.
Tests for documentation and code style (flake8) are also included in the testing suite.

It is also very strict regarding new code contributed to the project as it requires tests for said code/features to be included with the contribution in order to be accepted upstream.

On the other hand verification is not as important, seeing as there isn't really a formal specification or requirements document.
Most of the functionality available came from user or developer requests.

## Degree of Testability

### Controllability
(The degree to which it is possible to control the state of the component under test (CUT) as required for testing.)

### Observability
(The degree to which it is possible to observe (intermediate and final) test results.)

### Isolateability
(The degree to which the component under test (CUT) can be tested in isolation.)

### Separation of concerns
(The degree to which the component under test has a single, well defined responsibility.)

### Understandability

The modules and functionalities provided are self-explanatory . The concepts that are implemented are very well documented as see on [Documentation](https://docs.mopidy.com/en/latest/) making it easy ,even for newcomers, to understand the reach of the tests that are currently done and creating new ones for the said components. The tool used to write documentation is [Sphinx](http://sphinx-doc.org/) which is a python documentation generator making it possible to make a html where one can navigate through the components and check it's documentation.

### Heterogeneity

Through the use of [Travis CI](https://travis-ci.org) and [Tox](https://tox.readthedocs.org/en/latest/) and [pytest](http://pytest.org/latest/) all the submitted code is tested.Code coverage is  done using an external tool 
[coveralls.io](https://coveralls.io/github/mopidy/mopidy). Considering that mopidy only runs on Linux and MacOSX these are enough to guarantee proper testing. All the extensions developed are also tested under the same tools although they are not subject to the same scrutiny which leads to some of them lack of documentation and testing entirely .



## Test Statistics
There are **2056** tests total
