/* global $ */
/* global guild_id */
/* global guild_invite_url */

(function () {
    function query_guild() {
        var funct = $.ajax({
            dataType: "json",
            url: "/api/query_guild",
            data: {"guild_id": guild_id}
        });
        return funct.promise();
    }
    
    $(function(){
        $("#invite-waiting").hide();
        $("#invite-waiting-fail").hide();
        $("#invite-done").hide();
        
        $("#invite-btn").click(startInviteProcess);
    });
    
    function startInviteProcess() {
        $("#invite-initial").hide("slow");
        $("#invite-waiting").show("slow");
        window.open(guild_invite_url);
        query_guild_process(0);
    }

    function query_guild_process(index) {
        setTimeout(function() {
            var guild = query_guild();
            guild.done(function(data) {
                $("#invite-waiting").hide("slow");
                $("#invite-done").show("slow");
                return;
            });
            guild.fail(function(data) {
                if (data.status != 404 && data.status < 500) { // technically good
                    $("#invite-waiting").hide("slow");
                    $("#invite-done").show("slow");
                    return;
                } else if (index < 7) {
                    query_guild_process(index + 1);
                } else {
                    $("#invite-waiting").hide("slow");
                    $("#invite-waiting-fail").show("slow");
                    return;
                }
            });
        }, 5000);
    }
})();