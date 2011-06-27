***********
Data models
***********

These immutable data models are used for all data transfer within the Mopidy
backends and between the backends and the MPD frontend. All fields are optional
and immutable. In other words, they can only be set through the class
constructor during instance creation.


Data model relations
====================

.. digraph:: model_relations

    Playlist -> Track [ label="has 0..n" ]
    Track -> Album [ label="has 0..1" ]
    Track -> Artist [ label="has 0..n" ]
    Album -> Artist [ label="has 0..n" ]


Data model API
==============

.. automodule:: mopidy.models
    :synopsis: Data model API
    :members:
