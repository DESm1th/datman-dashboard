// This is needed to fix a firefox issue which
// causes iframes to become blank on page reload
$(document).ready(function() {
  var iframe = document.getElementById("papaya-viewer");
  iframe.parentNode.replaceChild(iframe.cloneNode(), iframe);
});


// Give focus to the iframe when mouse is over it so papaya keybindings
// still work
$("#papaya-viewer").mouseover(function() {
  this.focus();
});


$("#papaya-viewer").mouseout(function() {
  window.focus();
});


$('.open-viewer').off().on('click', function() {
  /* Update the papaya modal to display the scan associated with this button */
  var scanData = $(this)[0].dataset;

  // Load this scan in the viewer
  var viewer = $("#papaya-viewer")[0];
  viewer.setAttribute("src", scanData["url"]);

  // Display this scan's name in the modal
  var modalTitle = $("#papaya-scan-name")[0];
  modalTitle.innerText = scanData["name"];

});
