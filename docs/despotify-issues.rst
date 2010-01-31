Despotify issues
----------------

* r483: s.lookup('spotify:track:1mr3616BzLdhXfJmLmRsO8') returns error:
  "SpytifyError: URI specifies invalid type: track"
  Possibly fixed in r497.
* r483: When accessing an_artist.albums one get the error:
  "TypeError: Cannot convert spytify.AlbumDataFull to spytify.ArtistDataFull"
* r483: Sometimes segfaults when traversing stored playlists. May work if one
  try again immediately. Another example segfault::

    >>> In [45]: s.lookup('spotify:user:klette:playlist:5rOGYPwwKqbAcVX8bW4k5V')
    Segmentation fault

* r497: spytify fails on ``make''::

    src/spytify.c: In function ‘__pyx_pf_7spytify_7Spytify___init__’:
    src/spytify.c:7325: error: too few arguments to function ‘despotify_init_client’
