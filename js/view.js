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

function make_point(bldg_name, lat, long, map, bounds, FACILITIES_MODEL) {
  var name = bldg_name;
  var myLatLong = new google.maps.LatLng(lat, long);
  var marker = new google.maps.Marker({position: myLatLong, title:bldg_name});
  marker.setDraggable(true);
  marker.setMap(map); 
  google.maps.event.addListener(marker, 'mouseup', updateMarker);
  bounds.extend(myLatLong);
  FACILITIES_MODEL[name] = {'name':name, 'latlong':(myLatLong.toString())};			
}
