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

2. Enter the ``js/`` dir and install development dependencies::

       cd js/
       npm install

That's it.

You can now run the tests::

    npm test

To run tests automatically when you save a file::

    npm run-script watch

To run tests, concatenate, minify the source, and update the JavaScript files
in ``mopidy/frontends/http/data/``::

    npm run-script build

To run other `grunt <http://gruntjs.com/>`_ targets which isn't predefined in
``package.json`` and thus isn't available through ``npm run-script``::

    PATH=./node_modules/.bin:$PATH grunt foo
