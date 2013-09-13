$().ready(function() {
	page = 0
	submit= function() {
		bounds = gmaps.getBounds();
		ne = bounds.getNorthEast();
		sw = bounds.getSouthWest();
		lat1 = ne.lat();
		lon1 = ne.lng();
		lat2 = sw.lat();
		lon2 = sw.lng();
		$('.statusbar').html('Made request. The server is building your personal map... (Can take up to 45 seconds).');
		var jqXHR = $.get('/make/?lat1='+lat1+'&lon1='+lon1+'&lat2='+lat2+'&lon2='+lon2+'&game='+game).done(function(data){
			url=data;
			$('.statusbar').html('Success');
			$('#header').html('Map Created!');
			$('.lead').text('Let\'s set up your new map!');
		    $('#focusarea').html(['<ol>'+
		    	'<li>Download your map from <a href="'+url+'">here</a> (renamining it if you like to be more rememberable)</li>'+
		    	'<li>Copy the downloaded .bsp folder to C:/Program Folder(x86)/Steam/steamapps/common(garry\'s mod only)|accountname(everything else)/gamename/variation_of_gamename/maps'+
		    	'<li>Start the game and select your map</li>'+
		    	'<li>Enjoy!</li>'+
		    	'</ol>'].join('\n')).css('display', 'inline');
		   	$('#nav').css('display', 'inline');
		   	$('#myModal').foundation('reveal', 'open');

		}).fail(function(){
			$('.statusbar').html("Couldn't create file. It may have been too large to process. Please try again with a smaller map.").css('background-color', '#c60f13').css('border-color', '#970b0e')
		});
		console.log(jqXHR);
	}
	zoomin= function() {
		$('.statusbar').html("You are zoomed out too far and we won\'t be able to make your map. Zoom in!").css('background-color', '#c60f13').css('border-color', '#970b0e');
	}
	zoomok= function() {
				$('.statusbar').html('This\'ll work. When you have your region ready <a class="red" target="_blank" onclick="submit()">click here</a>.').css('background-color', '#5da423').css('border-color', '#457a1a');
	}
	gmaps = new GMaps({
	  div: '#map',
	  lat: -12.043333,
	  lng: -77.028333,
	  zoom: 7,
	  zoom_changed: function(e) {
	  	if (e.zoom > 15) {
	  		zoomok();
	  	}
	  	else {
	  		zoomin();
	  	}
	  }
	});
	GMaps.geolocate({
	  success: function(position) {
	    gmaps.setCenter(position.coords.latitude, position.coords.longitude);
	  },
	  error: function(error) {
	  },
	  not_supported: function() {
	  },
	  always: function() {
	  }
	});
	$('#myModal').foundation('reveal', 'open');
	advance = function() {
		if (page === 0) {
			$('#content').fadeOut("slow", function(){
				$('#header').html('Lets Begin');
			    $('.lead').text('Select the game you want to generate');
			    $('#focusarea').html(['<select class="chosen-select" name="game" style="width=100px">'+
			    	'<option value="tf2">Team Fortress 2</option>'+
			    	'<option value="hl2">Half-Life 2</option>'+
			    	'<option value="css">Counter Strike: Source</option>'+
			    	'<option value="hl2mp">Half Life 2: Deathmatch</option>'+
			    	'<option value="gm">Garry\'s Mod</option>'+
			    	'</select>'].join('\n')).css('display', 'inline');
			    $('#content').fadeIn("slow");

			});

		}
		else if (page === 1) {
			game=$('.chosen-select option:selected').val()
			$('#myModal').foundation('reveal', 'close');
			$('.statusbar').slideDown();
		}
		else {
			$('#myModal').foundation('reveal', 'close');
		}
		page++;
	}
	}
);