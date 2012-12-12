/*global module:false*/
module.exports = function (grunt) {

    grunt.initConfig({
        meta: {
            banner: "/*! Mopidy.js - built " +
                "<%= grunt.template.today('yyyy-mm-dd') %>\n" +
                " * http://www.mopidy.com/\n" +
                " * Copyright (c) <%= grunt.template.today('yyyy') %> " +
                "Stein Magnus Jodal and contributors\n" +
                " * Licensed under the Apache License, Version 2.0 */"
        },
        dirs: {
            dest: "../mopidy/frontends/http/data"
        },
        lint: {
            files: ["grunt.js", "src/**/*.js", "test/**/*-test.js"]
        },
        buster: {
            test: {
                config: "buster.js"
            }
        },
        concat: {
            dist: {
                src: [
                    "<banner:meta.banner>",
                    "lib/bane-*.js",
                    "lib/when-*.js",
                    "src/mopidy.js"
                ],
                dest: "<%= dirs.dest %>/mopidy.js"
            }
        },
        min: {
            dist: {
                src: ["<banner:meta.banner>", "<config:concat.dist.dest>"],
                dest: "<%= dirs.dest %>/mopidy.min.js"
            }
        },
        watch: {
            files: "<config:lint.files>",
            tasks: "lint buster concat min"
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
                devel: true
            },
            globals: {}
        },
        uglify: {}
    });

    grunt.registerTask("default", "lint buster concat min");

    grunt.loadNpmTasks("grunt-buster");
};
