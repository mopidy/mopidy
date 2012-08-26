/**
 * @author Wouter van Wijk
 * 
 * communication with ws server
 * 
 */

//process results of list of playlists of the user
function handleGetplaylists (resultArr) {
/*<p><ul><li>Donec id elit non mi porta</li><li>Gravida at eget metus. Fusce dapibus.</li><li>Tellus ac cursus commodo</li></p>
              <p><a class="btn" href="#">More &raquo;</a></p>	
*/
	$('#plslist').empty();
	playlists.length = 0;
	//console.log(resultArr);
	resultToPlaylists(resultArr, playlists);
	//console.log(playlists);
	tmp = '';
	for(var i=0; i < playlists.length; i++) {
		var child = '<li><a href="#" id="' + playlists[i].uri + '"">' + playlists[i].name + '</a></li>';
		tmp += child;
	};
	$('#plslist').html(tmp);
	$('#plslist a').click( function() { return setPlaylist(this.id) } );
}

//process results of a returned playlist
function handlePlaylist (resultArr) {
	newplaylisturi = resultArr["uri"];
	playlists[ newplaylisturi ] = resultArr;
	playlisttotable(playlists[newplaylisturi], '#pltable');
	currentviewuri = newplaylisturi;
}

//process results of a returned playlist
function handleCurrentPlaylist (resultArr) {
	console.log(resultArr)
	//$("#result").html(resultArr);
}

function handleSearchResults (searchtype, resultArr) {
	//div id is albumresulttable
	console.log(searchtype);
	console.log(resultArr);
	tableid = '#' + searchtype + 'resulttable'
	playlisttotable(resultArr, tableid);
}

