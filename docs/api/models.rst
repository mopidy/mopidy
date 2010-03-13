*********************************************
:mod:`mopidy.models` -- Immutable data models
*********************************************

.. automodule:: mopidy.models
    :synopsis: Immutable data models.
    :members:
    :undoc-members:

Model relations
===============

.. digraph:: model_relations

    Playlist -> Track [ label="has multiple" ]
    Track -> Album [ label="has one" ]
    Track -> Artist [ label="has multiple" ]
    Album -> Artist [ label="has multiple" ]
