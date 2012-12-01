/*jslint browser: true, plusplus: true */

/**
 * From
 * http://skratchdot.com/2012/05/prevent-console-calls-from-throwing-errors/
 */

(function (window) {
    'use strict';

    var i = 0,
        emptyFunction = function () {},
        functionNames = [
            'assert', 'clear', 'count', 'debug', 'dir',
            'dirxml', 'error', 'exception', 'group', 'groupCollapsed',
            'groupEnd', 'info', 'log', 'profile', 'profileEnd', 'table',
            'time', 'timeEnd', 'timeStamp', 'trace', 'warn'
        ];

    // Make sure window.console exists
    window.console = window.console || {};

    // Make sure all functions exist
    for (i = 0; i < functionNames.length; i++) {
        window.console[functionNames[i]] = window.console[functionNames[i]] || emptyFunction;
    }
}(window));
