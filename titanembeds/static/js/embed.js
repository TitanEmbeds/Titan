/* global $ */
/* global Materialize */
/* global Mustache */
/* global guild_id */
/* global bot_client_id */
/* global moment */

var logintimer; // timer to keep track of user inactivity after hitting login
var fetchtimeout; // fetch routine timer
var last_message_id; // last message tracked
var selected_channel = guild_id; // user selected channel, defaults to #general channel

function element_in_view(element, fullyInView) {
    var pageTop = $(window).scrollTop();
    var pageBottom = pageTop + $(window).height();
    var elementTop = $(element).offset().top;
    var elementBottom = elementTop + $(element).height();

    if (fullyInView === true) {
        return ((pageTop < elementTop) && (pageBottom > elementBottom));
    } else {
        return ((elementTop <= pageBottom) && (elementBottom >= pageTop));
    }
}

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
        data: {"guild_id": guild_id,"channel_id": channel_id, "after": after}
    });
    return funct.promise();
}

function post(channel_id, content) {
    var funct = $.ajax({
        method: "POST",
        dataType: "json",
        url: "/api/post",
        data: {"guild_id": guild_id, "channel_id": channel_id, "content": content}
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
    fill_channels(guildobj.channels);
    fill_discord_members(guildobj.discordmembers);
    fill_authenticated_users(guildobj.embedmembers.authenticated);
    fill_unauthenticated_users(guildobj.embedmembers.unauthenticated);
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
    $("#channel-"+selected_channel).parent().addClass("active");
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

function select_channel(channel_id) {
    if (selected_channel != channel_id) {
        selected_channel = channel_id;
        last_message_id = null;
        $("#channels-list > li.active").removeClass("active");
        $("#channel-"+selected_channel).parent().addClass("active");
        clearTimeout(fetchtimeout);
        run_fetch_routine();
    }
}

function replace_message_mentions(message) {
    var mentions = message.mentions;
    for (var i = 0; i < mentions.length; i++) {
        var mention = mentions[i];
        message.content = message.content.replace(new RegExp("<@" + mention.id + ">", 'g'), "@" + mention.username + "#" + mention.discriminator);
        message.content = message.content.replace(new RegExp("<@!" + mention.id + ">", 'g'), "@" + mention.username + "#" + mention.discriminator);
    }
    return message;
}

function getPosition(string, subString, index) {
   return string.split(subString, index).join(subString).length;
}

function format_bot_message(message) {
    if (message.author.id == bot_client_id && (message.content.includes("**") && ( (message.content.includes("<")&&message.content.includes(">")) || (message.content.includes("[") && message.content.includes("]")) ))) {
        var usernamefield = message.content.substring(getPosition(message.content, "**", 1)+3, getPosition(message.content, "**", 2)-1);
        message.content = message.content.substring(usernamefield.length+7);
        message.author.username = usernamefield.split("#")[0];
        message.author.discriminator = usernamefield.split("#")[1];
    }
    return message;
}

function parse_message_time(message) {
    var mome = moment(message.timestamp);
    message.formatted_timestamp = mome.toDate().toString();
    message.formatted_time = mome.format("HH:mm A");
    return message;
}

function fill_discord_messages(messages, jumpscroll) {
    if (messages.length == 0) {
        return last_message_id;
    }
    var last = 0;
    var template = $('#mustache_usermessage').html();
    Mustache.parse(template);
    for (var i = messages.length-1; i >= 0; i--) {
        var message = messages[i];
        message = replace_message_mentions(message);
        message = format_bot_message(message);
        message = parse_message_time(message);
        var rendered = Mustache.render(template, {"id": message.id, "full_timestamp": message.formatted_timestamp, "time": message.formatted_time, "username": message.author.username, "discriminator": message.author.discriminator, "content": message.content});
        $("#chatcontent").append(rendered);
        last = message.id;
    }
    $("html, body").animate({ scrollTop: $(document).height() }, "slow");
    return last;
}

function run_fetch_routine() {
    var channel_id = selected_channel;
    var fet;
    var jumpscroll;
    if (last_message_id == null) {
        $("#chatcontent").empty();
        fet = fetch(channel_id);
        jumpscroll = true;
    } else {
        fet = fetch(channel_id, last_message_id);
        jumpscroll = element_in_view($('#discordmessage_'+last_message_id), true);
    }
    fet.done(function(data) {
        var status = data.status;
        update_embed_userchip(status.authenticated, status.avatar, status.username, status.user_id);
        last_message_id = fill_discord_messages(data.messages, jumpscroll);
        if (status.manage_embed) {
            $("#administrate_link").show();
        } else {
            $("#administrate_link").hide();
        }
        var guild = query_guild();
        guild.done(function(guildobj) {
            fill_channels(guildobj.channels);
            fill_discord_members(guildobj.discordmembers);
            fill_authenticated_users(guildobj.embedmembers.authenticated);
            fill_unauthenticated_users(guildobj.embedmembers.unauthenticated);
            fetchtimeout = setTimeout(run_fetch_routine, 10000);
        });
    });
    fet.fail(function(data) {
        if (data.status == 403) {
            $('#loginmodal').modal('open');
            Materialize.toast('Authentication error! You have been disconnected by the server.', 10000);
        } else if (data.status == 401) {
            $('#loginmodal').modal('open');
            Materialize.toast('Session expired! You have been logged out.', 10000);
        }
    });
    fet.catch(function(data) {
      if (data.status != 403) {
          fetchtimeout = setTimeout(run_fetch_routine, 10000);
      }
    });
}

function update_embed_userchip(authenticated, avatar, username, userid) {
    if (authenticated) {
        $("#currentuserimage").show();
        $("#currentuserimage").attr("src", avatar);
        $("#currentusername").text(username);
    } else {
        $("#currentuserimage").hide();
        $("#currentusername").text(username + "#" + userid);
    }
    resize_messagebox();
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
            if (data.status == 429) {
              Materialize.toast('Sorry! You are allowed to log in as a guest once every 15 minutes.', 10000);
            } else if (data.status == 403) {
                Materialize.toast('Authentication error! You have been banned.', 10000);
            }
            unlock_login_fields();
        })
    }
});

$("#messagebox").keyup(function(event){
    if ($(this).val().length == 1) {
        $(this).val($.trim($(this).val()));
    }
    if(event.keyCode == 13 && $(this).val().length >= 1 && $(this).val().length <= 350) {
        $(this).val($.trim($(this).val()));
        $(this).blur();
        var funct = post(selected_channel, $(this).val());
        funct.done(function(data) {
            $("#messagebox").val("");
            clearTimeout(fetchtimeout);
            run_fetch_routine();
        });
        funct.fail(function(data) {
            Materialize.toast('Failed to send message.', 10000);
        });
        funct.catch(function(data) {
            if (data.status == 429) {
                Materialize.toast('You are sending messages too fast! 1 message per 10 seconds', 10000);
            }
        });
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
