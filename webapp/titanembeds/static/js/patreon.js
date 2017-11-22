/* global $, Materialize */
(function () {
    function post() {
        var funct = $.ajax({
            dataType: "json",
            method: "POST",
        });
        return funct.promise();
    }
    
    $("#syncbtn").click(function () {
        var formPost = post();
        formPost.done(function (data) {
            window.location.href = "thanks";
        });
        formPost.fail(function (data) {
            Materialize.toast('Failed to sync Patreon....', 10000);
        });
    });
})();