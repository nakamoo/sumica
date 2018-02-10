var UPDATE_TIMELINE = -1;
var UPDATE_CAMFEED = -1;
var USERNAME = "sean";
var SHOW_IMAGES = true;
var DEBUG = -1;
var UPDATE_STATES = true;

var url_string = window.location.href;
var url = new URL(url_string);

var c = url.searchParams.get("username");
if (c != null) {
    USERNAME = c;
}

var c = url.searchParams.get("states");
if (c != null) {
    UPDATE_STATES = parseInt(c) == 1;
}

var c = url.searchParams.get("d");
if (c != null) {
    DEBUG = parseInt(c);
}

var c = url.searchParams.get("feed");
if (c != null) {
    UPDATE_CAMFEED = parseInt(c);
}

var c = url.searchParams.get("timeline");
if (c != null) {
    UPDATE_TIMELINE = parseInt(c);
}

var c = url.searchParams.get("images");
if (c != null) {
    SHOW_IMAGES = parseInt(c) == 1;
}

var createuuid = function () {
    return Math.random().toString(16).substring(2, 14) + Math.random().toString(16).substring(2, 14);
};