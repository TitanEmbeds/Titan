/* global $ */
/* global Materialize */
/* global Mustache */
/* global guild_id */

var logintimer; // timer to keep track of user inactivity after hitting login

function resize_messagebox() {
    var namebox_width = $("#nameplate").outerWidth(true);
    var screen_width = $(document).width();
    $("#messageboxouter").width(screen_width - namebox_width - 40);
}

function query_guild() {
    var funct = $.ajax({
        dataType: "json",
        url: "/api/query_guild",
        data: {"guild_id": guild_id}
    });
    return funct.promise();
}

function create_authenticated_user() {
    var funct = $.ajax({
        method: "POST",
        dataType: "json",
        url: "/api/create_authenticated_user",
        data: {"guild_id": guild_id}
    });
    return funct.promise();
}

function create_unauthenticated_user(username) {
    var funct = $.ajax({
        method: "POST",
        dataType: "json",
        url: "/api/create_unauthenticated_user",
        data: {"username": username, "guild_id": guild_id}
    });
    return funct.promise();
}

function fetch(channel_id, after=null) {
    var funct = $.ajax({
        method: "GET",
        dataType: "json",
        url: "/api/fetch",
        data: {"channel_id": channel_id, "after": after}
    });
    return funct.promise();
}

$(function(){ 
  resize_messagebox();

    $("#loginmodal").modal({
        dismissible: false, // Modal can be dismissed by clicking outside of the modal
        opacity: .5, // Opacity of modal background
        inDuration: 300, // Transition in duration
        outDuration: 200, // Transition out duration
        startingTop: '4%', // Starting top style attribute
        endingTop: '10%', // Ending top style attribute
      }
    );
    
    var guild = query_guild();
    guild.fail(function() {
        $('#loginmodal').modal('open');
    });
    
    guild.done(function(data) {
        initialize_embed(data);
        //$('#loginmodal').modal('open');
    });
});

function lock_login_fields() {
    $("#loginProgress").show();
    $("#discordlogin_btn").attr("disabled",true);
    $("#custom_username_field").prop("disabled",true);
    logintimer = setTimeout(function() {
        unlock_login_fields();
    }, 60000);
}

function unlock_login_fields() {
    $("#loginProgress").hide();
    $("#discordlogin_btn").attr("disabled",false);
    $("#custom_username_field").prop("disabled",false);
    clearTimeout(logintimer);
}

function initialize_embed(guildobj) {
    $('#loginmodal').modal('close');
    unlock_login_fields();
    if (guildobj === undefined) {
        var guild = query_guild();
        guild.done(function(data) {
            prepare_guild(data);
        });
    } else {
        prepare_guild(guildobj);
    }
}

function prepare_guild(guildobj) {
    console.log(guildobj);
    fill_channels(guildobj.channels);
    fill_discord_members(guildobj.discordmembers);
    fill_authenticated_users(guildobj.embedmembers.authenticated);
    fill_unauthenticated_users(guildobj.embedmembers.unauthenticated);
    console.log("running fetch routine");
    run_fetch_routine();
}

function fill_channels(channels) {
    var template = $('#mustache_channellistings').html();
    Mustache.parse(template);
    $("#channels-list").empty();
    for (var i = 0; i < channels.length; i++) {
        var chan = channels[i];
        var rendered = Mustache.render(template, {"channelid": chan.id, "channelname": chan.name});
        $("#channels-list").append(rendered);
    }
}

function fill_discord_members(discordmembers) {
    var template = $('#mustache_authedusers').html();
    Mustache.parse(template);
    $("#discord-members").empty();
    for (var i = 0; i < discordmembers.length; i++) {
        var member = discordmembers[i];
        var rendered = Mustache.render(template, {"id": member.id, "username": member.username, "avatar": member.avatar_url});
        $("#discord-members").append(rendered);
    }
}

function fill_authenticated_users(users) {
    var template = $('#mustache_authedusers').html();
    Mustache.parse(template);
    $("#embed-discord-members").empty();
    for (var i = 0; i < users.length; i++) {
        var member = users[i];
        var rendered = Mustache.render(template, {"id": member.id, "username": member.username, "avatar": member.avatar_url});
        $("#embed-discord-members").append(rendered);
    }
}

function fill_unauthenticated_users(users) {
    var template = $('#mustache_unauthedusers').html();
    Mustache.parse(template);
    $("#embed-unauth-users").empty();
    for (var i = 0; i < users.length; i++) {
        var member = users[i];
        var rendered = Mustache.render(template, {"username": member.username, "discriminator": member.discriminator});
        $("#embed-unauth-users").append(rendered);
    }
}

function wait_for_discord_login() {
    _wait_for_discord_login(0);
}

function _wait_for_discord_login(index) {
    setTimeout(function() {
        var usr = create_authenticated_user();
        usr.done(function(data) {
            initialize_embed();
            return;
        });
        usr.fail(function(data) {
            if (data.status == 403) {
                Materialize.toast('Authentication error! You have been banned.', 10000);
            } else if (index < 10) {
                _wait_for_discord_login(index + 1);
            }
        });
    }, 5000);
}

function run_fetch_routine() {
    var channel_id = guild_id; //TODO: implement channel selector
    var fet = fetch(channel_id);
    fet.done(function(data) {
        console.log(data);
        
        var guild = query_guild();
        guild.done(function(guildobj) {
            fill_channels(guildobj.channels);
            fill_discord_members(guildobj.discordmembers);
            fill_authenticated_users(guildobj.embedmembers.authenticated);
            fill_unauthenticated_users(guildobj.embedmembers.unauthenticated);
            setTimeout(run_fetch_routine, 10000);
        });
    });
    fet.fail(function(data) {
            if (data.status == 403) {
                $('#loginmodal').modal('open');
                Materialize.toast('Authentication error! You have been banned.', 10000);
            }
            if (data.status == 401) {
                $('#loginmodal').modal('open');
                Materialize.toast('Session expired! You have been logged out.', 10000);
            }
            setTimeout(run_fetch_routine, 10000);
    });
}

$("#discordlogin_btn").click(function() {
    lock_login_fields();
    wait_for_discord_login();
});

$("#custom_username_field").keyup(function(event){
    if(event.keyCode == 13 && $(this).val().length >= 2 && $(this).val().length <= 32) {
        lock_login_fields();
        var usr = create_unauthenticated_user($(this).val());
        usr.done(function(data) {
            initialize_embed();
        });
        usr.fail(function(data) {
            if (data.status == 403) {
                Materialize.toast('Authentication error! You have been banned.', 10000);
            }
        })
    }
});

$(window).resize(function() {
    resize_messagebox();
});

$('#guild-btn').sideNav({
    menuWidth: 300, // Default is 300
    edge: 'left', // Choose the horizontal origin
    closeOnClick: true, // Closes side-nav on <a> clicks, useful for Angular/Meteor
    draggable: true // Choose whether you can drag to open on touch screens
}
);

$('#members-btn').sideNav({
    menuWidth: 300, // Default is 300
    edge: 'right', // Choose the horizontal origin
    draggable: true // Choose whether you can drag to open on touch screens
}
);