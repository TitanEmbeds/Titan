/* global $, Materialize, location */

function postForm(guild_id) {
    var funct = $.ajax({
        dataType: "json",
        method: "POST",
        data: {"guild_id": guild_id}
    });
    return funct.promise();
}

function deleteForm(guild_id) {
    var funct = $.ajax({
        dataType: "json",
        method: "DELETE",
        data: {"guild_id": guild_id}
    });
    return funct.promise();
}

$(function() {
    $("#new_submit").click(function () {
        var guild_id = $("#new_guild_id").val();
        if (guild_id.length < 1) {
            Materialize.toast("The server ID field can't be blank!", 2000);
            return;
        }
        var formPost = postForm(guild_id);
        formPost.done(function (data) {
            location.reload();
        });
        formPost.fail(function (data) {
            if (data.status == 409) {
                Materialize.toast('This server id already exists!', 10000);
            } else {
                Materialize.toast('Oh no! Something has failed submitting a new entry!', 10000);
            }
        });
    });
});

function delete_guild(guild_id) {
  var confirmation = confirm("Are you sure that you want to reenable server?");
  if (confirmation) {
    var formDelete = deleteForm(guild_id);
    formDelete.done(function (data) {
        location.reload();
    });
    formDelete.fail(function (data) {
        if (data.status == 409) {
            Materialize.toast('This server id does not exists!', 10000);
        } else {
            Materialize.toast('Oh no! Something has failed deleting this server entry!', 10000);
        }
    });
  }
}