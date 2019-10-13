function postForm(donation_goal_progress, donation_goal_total, donation_goal_end) {
    var funct = $.ajax({
        dataType: "json",
        method: "POST",
        data: {
            "donation_goal_progress": donation_goal_progress,
            "donation_goal_total": donation_goal_total,
            "donation_goal_end": donation_goal_end
        }
    });
    return funct.promise();
}

$("#submit").click(function () {
    Materialize.toast("Saving changes...", 2000);
    let donation_goal_progress = $("#donation_goal_progress").val();
    let donation_goal_total = $("#donation_goal_total").val();
    let donation_goal_end = $("#donation_goal_end").val();
    let req = postForm(donation_goal_progress, donation_goal_total, donation_goal_end);
    req.done(function () {
        Materialize.toast("All changes saved!", 2000);
    });
    req.fail(function () {
        Materialize.toast("There is an error saving changes.", 2000);
    });
});
