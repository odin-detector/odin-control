api_version = '0.1';

$( document ).ready(function() {

    update_api_version();
    update_api_adapters();
});

function update_api_version() {

    $.getJSON('/api', function(response) {
        api_version = response.api;
        $('#api-version').html(api_version);
    });
}

function update_api_adapters() {

    $.getJSON('/api/' + api_version + '/adapters/', function(response) {
        adapter_list = response.adapters.join(", ");
        $('#api-adapters').html(adapter_list);
    });
}
