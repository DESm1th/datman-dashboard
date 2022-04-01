$(document).ready(function() {
  /* This is needed to fix a firefox issue which causes iframes to become
     blank on page reload */
  var iframe = document.getElementById("papaya-viewer");
  iframe.parentNode.replaceChild(iframe.cloneNode(), iframe);
});


$("#papaya-viewer").mouseover(function() {
  /* Give focus to the iframe when mouse is over it so papaya keybindings work */
  this.focus();
});


$("#papaya-viewer").mouseout(function() {
  /* restore focus to window when mouse is outside iframe */
  window.focus();
});


$('.open-viewer').off().on('click', function() {
  /* Update the papaya modal to display the scan associated with the clicked
     button */
  var scanData = $(this)[0].dataset;

  // Load this scan in the viewer
  var viewer = $("#papaya-viewer")[0];
  viewer.setAttribute("src", scanData["url"]);

  // Display this scan's name in the modal
  var modalTitle = $("#papaya-scan-name")[0];
  modalTitle.innerText = scanData["name"];

  if (scanData["tag"] == "T1" || scanData["tag"] == "T2") {
    // If a scan is a T1/T2 hide the nav menu and make the viewer larger
    $("#papaya-nav").hide();
    $("#papaya-nav-col").removeClass("col-md-2");
    $("#papaya-viewer-col").removeClass("col-md-10");
  } else {
    // else, show the nav menu and make space for it in the modal
    $("#papaya-nav").show();
    $("#papaya-nav-col").addClass("col-md-2");
    $("#papaya-viewer-col").addClass("col-md-10");
  }

});


/* Papaya nav button functionality managed here */
var intervalHandler;
var frames = 3;

function loopSeries() {
  if (intervalHandler) {
    window.clearInterval(intervalHandler);
    intervalHandler = undefined;
    $("#loop-series").html('Play <i class="fas fa-play"></i>');
    $("#play-speed-controls").hide();
    $("#change-volume-controls").show();
    return
  }

  try {
    var viewer = document.getElementById("papaya-viewer").contentWindow.papayaContainers[0].viewer;
  } catch(err) {
    return
  }

  var speed = 1000 / frames;
  intervalHandler = window.setInterval(function() {
    if (viewer.currentScreenVolume.currentTimepoint < (viewer.volume.header.imageDimensions.timepoints - 1)) {
      viewer.incrementSeriesPoint();
    } else {
      // Loop to beginning
      viewer.currentScreenVolume.currentTimepoint = 1;
      viewer.decrementSeriesPoint();
    }
  }, speed);

  $("#play-speed").val(frames);
  $("#loop-series").html('Stop <i class="fas fa-stop"></i>');
  $("#play-speed-controls").show();
  $("#change-volume-controls").hide();
}


function updateSpeed() {
  frames = $("#play-speed").val();
  if (intervalHandler) {
    // stop first
    loopSeries();
  }
  loopSeries();
}


function decSlice() {
  /* View previous slice */
  document.getElementById('papaya-viewer').contentWindow.papayaContainers[0].viewer.decrementSeriesPoint();
}


function incSlice() {
  /* View next slice */
  document.getElementById('papaya-viewer').contentWindow.papayaContainers[0].viewer.incrementSeriesPoint();
}
