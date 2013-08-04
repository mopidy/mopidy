Mopidy.js
=========

Mopidy.js is a JavaScript library that is installed as a part of Mopidy's HTTP
frontend or from npm. The library makes Mopidy's core API available from the
browser or a Node.js environment, using JSON-RPC messages over a WebSocket to
communicate with Mopidy.


Getting it for browser use
--------------------------

Regular and minified versions of Mopidy.js, ready for use, is installed
together with Mopidy. When the HTTP frontend is running, the files are
available at:

- http://localhost:6680/mopidy/mopidy.js
- http://localhost:6680/mopidy/mopidy.min.js

You may need to adjust hostname and port for your local setup.

In the source repo, you can find the files at:

- `mopidy/frontends/http/data/mopidy.js`
- `mopidy/frontends/http/data/mopidy.min.js`


Getting it for Node.js use
--------------------------

If you want to use Mopidy.js from Node.js instead of a browser, you can install
Mopidy.js using npm:

    npm install mopidy

After npm completes, you can import Mopidy.js using ``require()``:

    var Mopidy = require("mopidy").Mopidy;


Using the library
-----------------

See Mopidy's [HTTP API
documentation](http://docs.mopidy.com/en/latest/api/http/).


Building from source
--------------------

1. Install [Node.js](http://nodejs.org/) and npm. There is a PPA if you're
   running Ubuntu:

        sudo apt-get install python-software-properties
        sudo add-apt-repository ppa:chris-lea/node.js
        sudo apt-get update
        sudo apt-get install nodejs

2. Enter the `js/` in Mopidy's Git repo dir and install all dependencies:

        cd js/
        npm install

That's it.

You can now run the tests:

    npm test

To run tests automatically when you save a file:

    npm start

To run tests, concatenate, minify the source, and update the JavaScript files
in `mopidy/frontends/http/data/`:

    npm run-script build

To run other [grunt](http://gruntjs.com/) targets which isn't predefined in
`package.json` and thus isn't available through `npm run-script`:

    PATH=./node_modules/.bin:$PATH grunt foo
