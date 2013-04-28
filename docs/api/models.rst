***********
Data models
***********

These immutable data models are used for all data transfer within the Mopidy
backends and between the backends and the MPD frontend. All fields are optional
and immutable. In other words, they can only be set through the class
constructor during instance creation.

If you want to modify a model, use the
:meth:`~mopidy.models.ImmutableObject.copy` method. It accepts keyword
arguments for the parts of the model you want to change, and copies the rest of
the data from the model you call it on. Example::

    >>> from mopidy.models import Track
    >>> track1 = Track(name='Christmas Carol', length=171)
    >>> track1
    Track(artists=[], length=171, name='Christmas Carol')
    >>> track2 = track1.copy(length=37)
    >>> track2
    Track(artists=[], length=37, name='Christmas Carol')
    >>> track1
    Track(artists=[], length=171, name='Christmas Carol')


Data model relations
====================

.. digraph:: model_relations

    Playlist -> Track [ label="has 0..n" ]
    Track -> Album [ label="has 0..1" ]
    Track -> Artist [ label="has 0..n" ]
    Album -> Artist [ label="has 0..n" ]

    SearchResult -> Artist [ label="has 0..n" ]
    SearchResult -> Album [ label="has 0..n" ]
    SearchResult -> Track [ label="has 0..n" ]


Data model API
==============

.. automodule:: mopidy.models
    :synopsis: Data model API
    :members:
