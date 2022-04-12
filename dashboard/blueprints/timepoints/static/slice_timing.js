function verifyTimings(tr) {
  /* Report issues with the user's slice timing input */
  var textBox = $('#new-timings')[0];

  textBox.setCustomValidity('');
  if (!textBox.validity.valid) {
    // Dont change the message if the contents are invalid for a reason
    // handled by the built in validators
    return;
  }

  var newTimings = $('#new-timings').val().trim().replace(/\[|\]/g, '').split(',');

  for (num = 0; num < newTimings.length; num++) {
    current = parseFloat(newTimings[num]);

    if (isNaN(current)) {
      textBox.setCustomValidity("Only numeric entries allowed");
      break;
    } else if (tr !== "N/A" && current > tr) {
      textBox.setCustomValidity("Entries must not be greater than the scan's TR");
      break;
    } else if (current < 0) {
      textBox.setCustomValidity("Entries must be non-negative");
      break;
    }
  }
  textBox.reportValidity();
}

$('.update-timings').off().on('click', function() {
  /* Update the slice timings modal with this scan's information.
  */
  var scanData = $(this).parent()[0].dataset;

  var expected = $('#timings-expected-' + scanData['scan'])[0];
  $('#timings-expected-display')[0].textContent = expected.textContent;

  var actual = $('#timings-actual-' + scanData['scan'])[0];
  $('#timings-actual-display')[0].textContent = actual.textContent;

  try {
    var tr = $('#tr-actual-' + scanData['scan'])[0].textContent;
  } catch {
    var tr = 'N/A';
  }

  $('#timings-tr-display')[0].textContent = tr;

  // Ensure user input is correct before submitting anything
  $('#submit-timings').off().on('click', function() {
    verifyTimings(tr);
  });

  // Submit data by Ajax query
  $('#slice-timing-form').off().on('submit', function(e) {
    e.preventDefault();

    scanData['timings'] = $('#new-timings').val();
    scanData['submit'] = true;
    scanData['csrf_token'] = csrfToken;

    $('#slice-timing-modal').modal('hide');

    function successFunc(response) {
      console.log('Updated successfully!');
    }

    function failFunc(response) {
      console.log('Failed updating!');
    }

    $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
              !this.crossDomain) {
              xhr.setRequestHeader('X-CSRFToken', csrfToken)
          }
      }
    });

    $.ajax({
      type: 'POST',
      url: sliceTimingUrl,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(scanData),
      success: successFunc,
      error: failFunc,
    });
  });
});
