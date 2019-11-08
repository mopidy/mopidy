.. _codestyle:

**********
Code style
**********

- Format with `Black <https://black.readthedocs.io/>`_.

- Follow :pep:`8` unless otherwise noted. `flake8
  <https://pypi.org/project/flake8>`_  should be used to check your code
  against the guidelines.

- Use four spaces for indentation, *never* tabs.

- Use CamelCase with initial caps for class names::

      ClassNameWithCamelCase

- Use underscore to split variable, function and method names for
  readability. Don't use CamelCase.

  ::

      lower_case_with_underscores

- Use the fact that empty strings, lists and tuples are :class:`False` and
  don't compare boolean values using ``==`` and ``!=``.

- Follow whitespace rules as described in :pep:`8`. Good examples::

      spam(ham[1], {eggs: 2})
      spam(1)
      dict['key'] = list[index]

- Limit lines to 80 characters and avoid trailing whitespace. However note that
  wrapped lines should be *one* indentation level in from level above, except
  for ``if``, ``for``, ``with``, and ``while`` lines which should have two
  levels of indentation::

      if (foo and bar ...
              baz and foobar):
          a = 1

      from foobar import (foo, bar, ...
          baz)

- For consistency, prefer ``'`` over ``"`` for strings, unless the string
  contains ``'``.

- Take a look at :pep:`20` for a nice peek into a general mindset useful for
  Python coding.
