var config = module.exports;

config["tests"] = {
    environment: "browser",
    libs: ["lib/**/*.js"],
    sources: ["src/**/*.js"],
    testHelpers: ["test/**/*-helper.js"],
    tests: ["test/**/*-test.js"]
};
