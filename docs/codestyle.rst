.. _codestyle:

**********
Code style
**********

All projects in the Mopidy organization follows the following code style:

- Automatically format all code with `Ruff <https://github.com/astral-sh/ruff>`_,
  using the default configuration.

- Automatically sort imports using Ruff_, using the default configuration.

- As far as reasonable and possible, comply with the lint warnings produced by
  Ruff_.

The strict adherence to Ruff are enforced by our CI setup.
Pull requests that do not pass these checks will not be merged.
