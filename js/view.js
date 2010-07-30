/* Function definitions for manipulating stuff in the view screen */

/*
// XXX GLOBALs in EVENTS FJFJSDJ:LKF!!!!
function updateMarker (event) {
  // updates global FACILITIES_MODEL on a button release (after dragging, in theory)
  FACILITIES_MODEL[this.title].latlong = this.getPosition().toString();
		
  // update point table
  var sel_lat = "#point_table #" + this.title + " #bldg_lat";
  $(sel_lat).html( this.getPosition().lat().toString());
  var sel_lon = "#point_table #" + this.title + " #bldg_lon";
  $(sel_lon).html( this.getPosition().lng().toString());
}
*/


function updateFacilities(fmodel, unguessable_id, comment) {
  // Upload changes to server.  Iterate over the markers, parse out the data,
  //     remunge into a string, get comments, build upload, and send home
  var upload_data = {
    'unguessable_id':unguessable_id,
    'model':JSON.stringify(fmodel),
    'comment':comment
  }; 
  var aj_params = {
    'type': 'POST',
    'url': './update',
    'data': upload_data,
    'success': function(data, textStatus, XMLHttpRequest){alert('Uploaded Data: ' + textStatus)}
  };
  $.ajax(aj_params);
}

// grab points in JSON for a given unguessable_id
function getPoints(unguessable_id){
  var result = null;
  $.ajax({
    async: false,
	url: "/buildingfeed",
	data: {'unguessable_id':unguessable_id},
	dataType: "json",
	success: function(data){
	result = data;
      }
    });
  return result;
}


// returns a function for a marker listener, with closure magic to retain a
//    reference to the global model
function mkMarkerListener(fmodel) {
  
  return function (event) {

    // updates a reference to global FACILITIES_MODEL on a button release (after dragging, in theory)
    fmodel[this.title].latlong = this.getPosition().toString();
    
    // update point table
    var sel_lat = "#point_table #" + this.title + " #bldg_lat";
    $(sel_lat).html( this.getPosition().lat().toString());
    var sel_lon = "#point_table #" + this.title + " #bldg_lon";
    $(sel_lon).html( this.getPosition().lng().toString());
  }
}

// make a point on the map, update bounds
function make_point(fmodel, gmap, bldg_name, lat, lng, bounds) {
  var name = bldg_name;
  var myLatLong = new google.maps.LatLng(lat, lng);
  var marker = new google.maps.Marker({position: myLatLong, title:bldg_name});
  marker.setDraggable(true);
  marker.setMap(gmap); 
  google.maps.event.addListener(marker, 'mouseup', mkMarkerListener(fmodel));
  bounds.extend(myLatLong);
}

// grab points, make map, update model
function make_map(fmodel, gmap, unguessable_id) {
  // set up the map
  gmap = new google.maps.Map(document.getElementById("map_canvas"), {mapTypeId: google.maps.MapTypeId.ROADMAP});
  var bounds = new google.maps.LatLngBounds();  
  
  // parse and iterate over each point and have make_point do the work
  var points = getPoints(unguessable_id);
  var points_str = '';
  for (var i = 0; i < points.length; i++) {
    make_point(fmodel, gmap, points[i].title, points[i].lat, points[i].lng, bounds);
    points_str = '(' +  points[i].lat + ',' + points[i].lng + ')';
    fmodel[points[i].title] = {'name':name, 'latlong':points_str};
    //alert(fmodel[points[i].title]['latlong']);
  } 

  // Zoom
  var sp = (bounds.toSpan().lat() + bounds.toSpan().lng()) ;
  if ( sp < 0.01) {
    gmap.setCenter(bounds.getCenter());
    gmap.setZoom(14); 
  }
  else {
    gmap.fitBounds(bounds);  
  }
}


