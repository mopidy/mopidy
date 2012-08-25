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
	updatePlaylist(newplaylisturi);
}

//process results of a returned playlist
function handleCurrentPlaylist (resultArr) {
	console.log(resultArr)
	//$("#result").html(resultArr);
}

function handleSearchAlbum (resultArr) {
	//div id is albumresulttable
	$('#albumresulttable').empty();
	resultToSonglist(resultArr, searchalbums);
	tmp = '';
	for(var i=0; i < searchalbums.length; i++) {
		var child = '<tr><td><a href="#" id="' + i + '">' + searchalbums[i].title +
			 '</a></td><td><a href="#" id="' + i + '">' + searchalbums[i].artist + 
			 '</a></td><td><a href="#" id="' + i + '">' + searchalbums[i].album + 
			 '</a></td><td><a href="# id="' + i + '">' + searchalbums[i].getTime + '</a></td></tr>';
		tmp += child;
	};
	$('#albumresulttable').html(tmp);
	$('#albumresulttable a').click( function() { return newPlaylist(searchalbums, 'Search Albums Results', this.id) } );	
}

function handleSearchTitle (resultArr) {
	//div id is trackresulttable
	$('#trackresulttable').empty();
	resultToSonglist(resultArr, searchtracks);
	tmp = '';
	for(var i=0; i < searchtracks.length; i++) {
		var child = '<tr><td><a href="#" id="' + i + '">' + searchtracks[i].title +
			 '</a></td><td><a href="#" id="' + i + '">' + searchtracks[i].artist + 
			 '</a></td><td><a href="#" id="' + i + '">' + searchtracks[i].album + 
			 '</a></td><td><a href="# id="' + i + '">' + searchtracks[i].getTime + '</a></td></tr>';
		tmp += child;
	};
	$('#trackresulttable').html(tmp);
	$('#trackresulttable a').click( function() { newPlaylist(searchtracks, 'Search Track Results', this.id) } );
}

function handleSearchArtist (resultArr) {
	//div id is artistresulttable
	$('#artistresulttable').empty();
	resultToPlaylist(resultArr, searchartists);
	tmp = '';
	for(var i=0; i < searchartists.length; i++) {
		var child = '<tr><td><a href="#" id="' + i + '">' + searchartists[i].title +
			 '</a></td><td><a href="#" id="' + i + '">' + searchartists[i].artist + 
			 '</a></td><td><a href="#" id="' + i + '">' + searchartists[i].album + 
			 '</a></td><td><a href="# id="' + i + '">' + searchartists[i].getTime + '</a></td></tr>';
		tmp += child;
	};
	$('#artistresulttable').html(tmp);
	$('#artistresulttable a').click( function() { newPlaylist(searchartists, 'Search Artist Results', this.id) } );
}
