/* global $ */
(function () {
    "use strict";
    function updateQueryParameters() {
        let baseURL = window.location.origin + "/embed/" + $("#queryparam_guildid").val();
        let inputs = $("input.queryparam");
        let url = baseURL;
        for (let i = 0; i < inputs.length; i++) {
            let input = $(inputs[i]);
            let name = input.attr("name");
            let value = input.val();
            if (!value) {
                continue;
            }
            if (!url.includes("?")) {
                url += "?";
            } else {
                url += "&";
            }
            url += `${name}=${value}`;
        }
        $("#queryparam_url").val(url);
    }
    
    $(function () {
        $("input.queryparam").change(updateQueryParameters);
        $("#queryparam_guildid").change(updateQueryParameters);
    });
})();