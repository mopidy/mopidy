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
                concat: "../mopidy/frontends/http/data/mopidy.js",
                minified: "../mopidy/frontends/http/data/mopidy.min.js"
            }
        },
        buster: {
            all: {}
        },
        concat: {
            options: {
                banner: "<%= meta.banner %>",
                stripBanners: true
            },
            all: {
                files: {
                    "<%= meta.files.concat %>": [
                        "lib/bane-*.js",
                        "lib/when-define-shim.js",
                        "lib/when-*.js",
                        "src/mopidy.js"
                    ]
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

    grunt.registerTask("test", ["jshint", "buster"]);
    grunt.registerTask("build", ["test", "concat", "uglify"]);
    grunt.registerTask("default", ["build"]);

    grunt.loadNpmTasks("grunt-buster");
    grunt.loadNpmTasks("grunt-contrib-concat");
    grunt.loadNpmTasks("grunt-contrib-jshint");
    grunt.loadNpmTasks("grunt-contrib-uglify");
    grunt.loadNpmTasks("grunt-contrib-watch");
};
