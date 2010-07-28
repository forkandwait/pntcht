/* Function definitions for manipulating stuff in the view screen */

function updateMarker (event) {
  // updates global FACILITIES_MODEL on a button release (after dragging, in theory)
  FACILITIES_MODEL[this.title].latlong = this.getPosition().toString();
		
  // update point table -- doesn't work yet, WITH SPACES IN BUILDING NAMES
  var sel_lat = "#point_table #" + this.title + " #bldg_lat";
  $(sel_lat).html( this.getPosition().lat().toString());
  var sel_lon = "#point_table #" + this.title + " #bldg_lon";
  $(sel_lon).html( this.getPosition().lng().toString());
}
	
function updateFacilities(FACILITIES_MODEL, UNGUESSABLE_ID, comment) {
  // Upload changes to server.  Iterate over the markers, parse out the data,
  //     remunge into a string, get comments, build upload, and send home
  var upload_data = {
    unguessable_id:UNGUESSABLE_ID,
    model:JSON.stringify(FACILITIES_MODEL),
    comment:comment
  }; 
  var aj_params = {
    type: 'POST',
    url: './update',
    data: upload_data,
    success: function(data, textStatus, XMLHttpRequest){alert('Uploaded Data: ' + textStatus)}
  };
  $.ajax(aj_params);
}

function make_point(bldg_name, lat, long, gmap, bounds, FACILITIES_MODEL) {
  var name = bldg_name;
  var myLatLong = new google.maps.LatLng(lat, long);
  var marker = new google.maps.Marker({position: myLatLong, title:bldg_name});
  marker.setDraggable(true);
  marker.setMap(gmap); 
  google.maps.event.addListener(marker, 'mouseup', updateMarker);
  bounds.extend(myLatLong);
  FACILITIES_MODEL[name] = {'name':name, 'latlong':(myLatLong.toString())};			
}


function make_map_xml(FMODEL, gmap, markers_xml) {
  // TODO -- make this grab from a KML feed rather than generated code (blech!) 
  
  gmap = new google.maps.Map(document.getElementById("map_canvas"), {mapTypeId: google.maps.MapTypeId.ROADMAP});
  
  // Facilities markers -- generate a bunch of JS 
  //    via django template loop, store array globally.
  var name = "";
  var myLatLong = "";
  var marker = "";
  var bounds = new google.maps.LatLngBounds();
  //{% for bldg in bldg_table %}
  //make_point("{{ bldg.name }}", {{ bldg.pt }}, gmap, bounds, fmodel);  // XXX bldg.pt expands 
  //{% Endfor %}
  
  // Zoom
  gmap.setCenter(bounds.getCenter());
  gmap.setZoom(14); 
}


