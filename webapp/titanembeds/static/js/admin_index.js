/* global $ */
/* global Materialize */

(function () {
    function cleanup_database() {
        var funct = $.ajax({
            method: "DELETE",
            url: "/api/cleanup-db",
        });
        return funct.promise();
    }
    
    $(function(){
        $("#db_cleanup_btn").click(run_cleanup_db);
    });
    
    function run_cleanup_db() {
        $("#db_cleanup_btn").attr("disabled",true);
        Materialize.toast('Please wait for the cleanup database task to finish...', 10000);
        var cleanupdb = cleanup_database();
        cleanupdb.done(function () {
            $("#db_cleanup_btn").attr("disabled",false);
            Materialize.toast('Successfully cleaned up the database!', 10000);
        });
        cleanupdb.fail(function () {
            $("#db_cleanup_btn").attr("disabled",false);
            Materialize.toast('Database cleanup failiure.', 10000);
        });
    }
})();