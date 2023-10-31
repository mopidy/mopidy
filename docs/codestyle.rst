.. _codestyle:

**********
Code style
**********

All projects in the Mopidy organization follows the following code style:

- Automatically format all code with `Black <https://black.readthedocs.io/>`_,
  using the default configuration.

- Automatically sort imports using `Ruff <https://github.com/astral-sh/ruff>`_,
  using the default configuration.

- As far as reasonable and possible, comply with the lint warnings produced by
  Ruff.

The strict adherence to Black and Ruff are enforced by our CI setup.
Pull requests that do not pass these checks will not be merged.
