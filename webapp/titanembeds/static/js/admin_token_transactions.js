/* global $, Materialize, location */

function postForm(user_id, amount) {
    var funct = $.ajax({
        dataType: "json",
        method: "POST",
        data: {"user_id": user_id, "amount": amount}
    });
    return funct.promise();
}

function patchForm(user_id, amount) {
    var funct = $.ajax({
        dataType: "json",
        method: "PATCH",
        data: {"user_id": user_id, "amount": amount}
    });
    return funct.promise();
}

$(function() {
    $("#new_submit").click(function () {
        var user_id = $("#new_user_id").val();
        var user_token = $("#new_user_token").val();
        if (user_id.length < 1 || user_token.length < 1) {
            Materialize.toast("The user ID or balance field can't be blank!", 2000);
            return;
        }
        var formPost = postForm(user_id, user_token);
        formPost.done(function (data) {
            location.reload();
        });
        formPost.fail(function (data) {
            if (data.status == 409) {
                Materialize.toast('This user id already exists!', 10000);
            } else {
                Materialize.toast('Oh no! Something has failed submitting a new entry!', 10000);
            }
        });
    });
});

function submit_modify_user(user_id) {
    var amount = $("#input_"+user_id).val();
    var formPatch = patchForm(user_id, amount);
    formPatch.done(function (data) {
        location.reload();
    });
    formPatch.fail(function (data) {
        if (data.status == 409) {
            Materialize.toast('This user id does not exists!', 10000);
        } else {
            Materialize.toast('Oh no! Something has failed changing the css toggle!', 10000);
        }
    });
}