/*global module:false*/
module.exports = function (grunt) {

    grunt.initConfig({
        meta: {
            banner: "/*! Mopidy.js - built " +
                "<%= grunt.template.today('yyyy-mm-dd') %>\n" +
                " * http://www.mopidy.com/\n" +
                " * Copyright (c) <%= grunt.template.today('yyyy') %> " +
                "Stein Magnus Jodal and contributors\n" +
                " * Licensed under the Apache License, Version 2.0 */\n",
            files: {
                own: ["Gruntfile.js", "src/**/*.js", "test/**/*-test.js"],
                main: "src/mopidy.js",
                concat: "../mopidy/http/data/mopidy.js",
                minified: "../mopidy/http/data/mopidy.min.js"
            }
        },
        buster: {
            all: {}
        },
        browserify: {
            test_mopidy: {
                files: {
                    "test/lib/mopidy.js": "<%= meta.files.main %>"
                },
                options: {
                    postBundleCB: function (err, src, next) {
                        next(null, grunt.template.process("<%= meta.banner %>") + src);
                    },
                    standalone: "Mopidy"
                }
            },
            test_when: {
                files: {
                    "test/lib/when.js": "node_modules/when/when.js"
                },
                options: {
                    standalone: "when"
                }
            },
            dist: {
                files: {
                    "<%= meta.files.concat %>": "<%= meta.files.main %>"
                },
                options: {
                    postBundleCB: function (err, src, next) {
                        next(null, grunt.template.process("<%= meta.banner %>") + src);
                    },
                    standalone: "Mopidy"
                }
            }
        },
        jshint: {
            options: {
                curly: true,
                eqeqeq: true,
                immed: true,
                indent: 4,
                latedef: true,
                newcap: true,
                noarg: true,
                sub: true,
                quotmark: "double",
                undef: true,
                unused: true,
                eqnull: true,
                browser: true,
                devel: true,
                globals: {}
            },
            files: "<%= meta.files.own %>"
        },
        uglify: {
            options: {
                banner: "<%= meta.banner %>"
            },
            all: {
                files: {
                    "<%= meta.files.minified %>": ["<%= meta.files.concat %>"]
                }
            }
        },
        watch: {
            files: "<%= meta.files.own %>",
            tasks: ["default"]
        }
    });

    grunt.registerTask("test_build", ["browserify:test_when", "browserify:test_mopidy"]);
    grunt.registerTask("test", ["jshint", "test_build", "buster"]);
    grunt.registerTask("build", ["test", "browserify:dist", "uglify"]);
    grunt.registerTask("default", ["build"]);

    grunt.loadNpmTasks("grunt-buster");
    grunt.loadNpmTasks("grunt-browserify");
    grunt.loadNpmTasks("grunt-contrib-jshint");
    grunt.loadNpmTasks("grunt-contrib-uglify");
    grunt.loadNpmTasks("grunt-contrib-watch");
};
