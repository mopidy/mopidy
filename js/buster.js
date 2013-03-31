var config = module.exports;

config.browser_tests = {
    environment: "browser",
    libs: [
        "lib/bane-*.js",
        "lib/when-define-shim.js",
        "lib/when-*.js"
    ],
    sources: ["src/**/*.js"],
    testHelpers: ["test/**/*-helper.js"],
    tests: ["test/**/*-test.js"]
};

config.node_tests = {
    environment: "node",
    libs: [
        "lib/bane-*.js",
        "lib/when-define-shim.js",
        "lib/when-*.js"
    ],
    sources: ["src/**/*.js"],
    testHelpers: ["test/**/*-helper.js"],
    tests: ["test/**/*-test.js"]
};
