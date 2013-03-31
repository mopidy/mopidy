if (typeof window !== "undefined") {
    window.define = function (factory) {
        try {
            delete window.define;
        } catch (e) {
            window.define = void 0; // IE
        }
        window.when = factory();
    };
    window.define.amd = {};
}
