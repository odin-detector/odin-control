$( document ).ready(function() {

    update_api_version();

});

function update_api_version() {

    $.getJSON('/api', function(response) {
        $('#api-version').html(response.api_version);
    });
}
