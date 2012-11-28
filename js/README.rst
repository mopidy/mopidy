*********
Mopidy.js
*********

This is the source for the JavaScript library that is installed as a part of
Mopidy's HTTP frontend. The library makes Mopidy's core API available from the
browser, using JSON-RPC messages over a WebSocket to communicate with Mopidy.


Getting it
==========

Regular and minified versions of Mopidy.js, ready for use, is installed
together with Mopidy. When the HTTP frontend is running, the files are
available at:

- http://localhost:6680/mopidy/mopidy.js
- http://localhost:6680/mopidy/mopidy.min.js

You may need to adjust hostname and port for your local setup.

In the source repo, you can find the files at:

- ``mopidy/frontends/http/data/mopidy.js``
- ``mopidy/frontends/http/data/mopidy.min.js``


Building from source
====================

1. Install `Node.js <http://nodejs.org/>`_ and npm. There is a PPA if you're
   running Ubuntu::

       sudo apt-get install python-software-properties
       sudo add-apt-repository ppa:chris-lea/node.js
       sudo apt-get update
       sudo apt-get install nodejs npm

2. Assuming you install from PPA, setup your ``NODE_PATH`` environment variable
   to include ``/usr/lib/node_modules``. Add the following to your
   ``~/.bashrc`` or equivalent::

       export NODE_PATH=/usr/lib/node_modules:$NODE_PATH

3. Install `Buster.js <http://busterjs.org/>`_ and `Grunt
   <http://gruntjs.com/>`_ globally (or locally, and make sure you get their
   binaries on your ``PATH``)::

       sudo npm -g install buster grunt

4. Install the grunt-buster Grunt plugin locally, when in the ``js/`` dir::

       cd js/
       npm install grunt-buster

5. Run Grunt to lint, test, concatenate, and minify the source::

       grunt

   The files in ``../mopidy/frontends/http/data/`` should now be up to date.


Development tips
================

If you're coding on the JavaScript library, you should know about ``grunt
watch``. It lints and tests the code every time you save a file.
