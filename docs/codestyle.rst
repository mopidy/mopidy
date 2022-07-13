.. _codestyle:

**********
Code style
**********

All projects in the Mopidy organization follows the following code style:

- Automatically format all code with `Black <https://black.readthedocs.io/>`_.
  Use Black's string normalization, which prefers ``"`` quotes over ``'``,
  unless the string contains ``"``.

- Automatically sort imports using `isort <https://timothycrosley.github.io/isort>`_.
  
- Follow :pep:`8`.
  Run `flake8 <https://pypi.org/project/flake8>`_  to check your code
  against the guidelines.

The strict adherence to Black and flake8 are enforced by our CI setup.
Pull requests that do not pass these checks will not be merged.

For more general advise,
take a look at :pep:`20` for a nice peek into a general mindset
useful for Python coding.
