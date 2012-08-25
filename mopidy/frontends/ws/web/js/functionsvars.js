/**
 * @author Wouter van Wijk
 * 
 * all kinds functions and vars  
 */

var baseurl = '/mopidy';
var host = window.location.hostname;
var port = window.location.port;
var wsurl = host + ':' + port + baseurl
var intv;
var socket;

//uri of current playlist/album/artist 
var currentviewuri = 'none';
var nowplayinguri = '';

//values for controls
var play 
var shuffle; 
var repeat; 
var currentVolume = -1;
var muteVol = -1;

//array of used playlists
var playlists = new Array();
var searchartists = new Array();
var searchalbums = new Array();
var searchtracks = new Array();

WEB_SOCKET_SWF_LOCATION = "/static/WebSocketMain.swf";
WEB_SOCKET_DEBUG = true;


//convert time to human readable format  
function timeFromSeconds (length) {
	d = Number(length);
	var h = Math.floor(d / 3600);
	var m = Math.floor(d % 3600 / 60);
	var s = Math.floor(d % 3600 % 60);
	return ((h > 0 ? h + ":" : "") + (m > 0 ? (h > 0 && m < 10 ? "0" : "") + m + ":" : "0:") + (s < 10 ? "0" : "") + s);
}
	
//playlist object
function playlist(name, uri, tracks) {
	this.uri = uri;
	this.name = name;
	//array of track
	this.tracks = tracks;
}

//track object
function track(uri, length, artists, name, albumname, albumuri) {
	this.uri = uri;
	this.name = name;
//  aray of artists
	this.artists = artists;
	this.albumname = albumname;
	this.albumuri = albumuri;
	this.length = length;
}

//convert mopidy results to a playlist list
function resultToPlaylists(resultArr, nwplaylists) {
	//get list of playlists from server result
	for(var i=0; i < resultArr.length; i++) {
		nwplaylists.push (new playlist(resultArr[i][0], resultArr[i][1]));
	}
}

