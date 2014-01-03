var config = module.exports;

config.browser_tests = {
    environment: "browser",
    libs: ["test/lib/*.js"],
    testHelpers: ["test/**/*-helper.js"],
    tests: ["test/**/*-test.js"]
};

config.node_tests = {
    environment: "node",
    sources: ["src/**/*.js"],
    testHelpers: ["test/**/*-helper.js"],
    tests: ["test/**/*-test.js"]
};
