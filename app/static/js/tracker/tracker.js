

function updateOutput (data='') {
    // Pre-beautify data if it's JSON.
    if (!(data instanceof String) && typeof data === 'object')
        data = JSON.stringify(data, null, 2);

    var output = document.getElementById('output-data');
    output.textContent = data;
}

async function getTrackingInfo () {
    // Clear output.
    updateOutput();

    // Request tracking info through API.
    url = new URL('/api/tracker', window.location.origin)
    url.search = new URLSearchParams({
        'tracking_number': document.getElementById('tracking_number').value
    }).toString();
    let response = await fetch(url);
    let data = await response.json();

    return data;
}

function trackerSubmit() {
    // Main function: will be called on form submit.
    getTrackingInfo()
        .then(data => updateOutput(data))
        .catch(reason => updateOutput(reason.message));
}