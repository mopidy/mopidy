var config = module.exports;

config.browser_tests = {
    environment: "browser",
    libs: ["lib/**/*.js"],
    sources: ["src/**/*.js"],
    testHelpers: ["test/**/*-helper.js"],
    tests: ["test/**/*-test.js"]
};

config.node_tests = {
    environment: "node",
    libs: ["lib/**/*.js"],
    sources: ["src/**/*.js"],
    testHelpers: ["test/**/*-helper.js"],
    tests: ["test/**/*-test.js"]
};
