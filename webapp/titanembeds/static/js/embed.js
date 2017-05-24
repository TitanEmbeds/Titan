/* global $ */
/* global Materialize */
/* global Mustache */
/* global guild_id */
/* global bot_client_id */
/* global moment */

(function () {
    var has_already_been_focused = false; // keep track of if the embed has initially been focused.
    var logintimer; // timer to keep track of user inactivity after hitting login
    var fetchtimeout; // fetch routine timer
    var currently_fetching; // fetch lock- if true, do not fetch
    var last_message_id; // last message tracked
    var selected_channel = guild_id; // user selected channel, defaults to #general channel
    var guild_channels = {}; // all server channels used to highlight channels in messages
    var times_fetched = 0; // kept track of how many times that it has fetched
    var fetch_error_count = 0; // Number of errors fetch has encountered
    var priority_query_guild = false; // So you have selected a channel? Let's populate it.

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
    
    $(function() {
        $("#focusmodal").modal({
            dismissible: true,
            opacity: .5,
            inDuration: 400,
            outDuration: 400,
            startingTop: "4%",
            endingTop: "10%",
        });
        $("#focusmodal").modal("open");
        
        if (document.hasFocus()) {
            primeEmbed();
        }
        
        $(window).focus(function() {
            if (!has_already_been_focused) {
                primeEmbed();
            }
        });
    });

    function primeEmbed() {
        $("#focusmodal").modal("close");
        has_already_been_focused = true;
        
        $("#loginmodal").modal({
            dismissible: false, // Modal can be dismissed by clicking outside of the modal
            opacity: .5, // Opacity of modal background
            inDuration: 300, // Transition in duration
            outDuration: 200, // Transition out duration
            startingTop: '4%', // Starting top style attribute
            endingTop: '10%', // Ending top style attribute
          }
        );
        $('#loginmodal').modal('open');
        lock_login_fields();

        var guild = query_guild();
        guild.fail(function() {
            unlock_login_fields();
        });

        guild.done(function(data) {
            initialize_embed(data);
        });
    }

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
        if (guildobj === undefined) {
            var guild = query_guild();
            guild.done(function(data) {
                prepare_guild(data);
                $('#loginmodal').modal('close');
                unlock_login_fields();
            });
        } else {
            prepare_guild(guildobj);
            $('#loginmodal').modal('close');
            unlock_login_fields();
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
            guild_channels[chan.channel.id] = chan;
            if (chan.read) {
              var rendered = Mustache.render(template, {"channelid": chan.channel.id, "channelname": chan.channel.name});
              $("#channels-list").append(rendered);
              $("#channel-" + chan.channel.id.toString()).click({"channel_id": chan.channel.id.toString()}, function(event) {
                  select_channel(event.data.channel_id);
              });
              if (chan.channel.id == selected_channel) {
                if (chan.write) {
                  $("#messagebox").prop('disabled', false);
                  $("#messagebox").prop('placeholder', "Enter message");
                } else {
                  $("#messagebox").prop('disabled', true);
                  $("#messagebox").prop('placeholder', "Messages is disabled in this channel.");
                }
                $("#channeltopic").text(chan.channel.topic);
              }
            }
        }
        $("#channel-"+selected_channel).parent().addClass("active");
    }

    function mention_member(member_id) {
      if (!$('#messagebox').prop('disabled')) {
        $('#messagebox').val( $('#messagebox').val() + "[@" + member_id + "] " );
        $('.button-collapse').sideNav('hide');
        $("#messagebox").focus();
      }
    }

    function fill_discord_members(discordmembers) {
        var template = $('#mustache_authedusers').html();
        Mustache.parse(template);
        $("#discord-members").empty();
        var guild_members = {};
        for (var i = 0; i < discordmembers.length; i++) {
            var member = discordmembers[i];
            if (member["hoist-role"]) {
              if (!(member["hoist-role"]["id"] in guild_members)) {
                guild_members[member["hoist-role"]["id"]] = {};
                guild_members[member["hoist-role"]["id"]]["name"] = member["hoist-role"]["name"];
                guild_members[member["hoist-role"]["id"]]["members"] = [];
                guild_members[member["hoist-role"]["id"]]["position"] = member["hoist-role"]["position"];
              }
              guild_members[member["hoist-role"]["id"]]["members"].push(member);
            } else {
              if (!("0" in guild_members)) {
                guild_members["0"] = {};
                guild_members["0"]["name"] = null;
                guild_members["0"]["members"] = [];
                guild_members["0"]["position"] = 0;
              }
              guild_members["0"]["members"].push(member);
            }
        }
        var guild_members_arr = [];
        for (var key in guild_members) {
          guild_members_arr.push(guild_members[key]);
        }
        guild_members_arr.sort(function(a, b) {
          return parseInt(b.position) - parseInt(a.position);
        });
        var template_role = $('#mustache_memberrole').html();
        Mustache.parse(template_role);
        var template_user = $('#mustache_authedusers').html();
        Mustache.parse(template_user);
        $("#discord-members").empty();
        var discordmembercnt = 0;
        for (var i = 0; i < guild_members_arr.length; i++) {
          var roleobj = guild_members_arr[i];
          if (!roleobj["name"]) {
            roleobj["name"] = "Uncategorized";
          }
          var rendered_role = Mustache.render(template_role, {"name": roleobj["name"] + " - " + roleobj["members"].length});
          discordmembercnt += roleobj["members"].length;
          $("#discord-members").append(rendered_role);
          for (var j = 0; j < roleobj.members.length; j++) {
            var member = roleobj.members[j];
            var rendered_user = Mustache.render(template_user, {"id": member.id.toString() + "d", "username": member.username, "avatar": member.avatar_url});
            $("#discord-members").append(rendered_user);
            $( "#discorduser-" + member.id.toString() + "d").click({"member_id": member.id.toString()}, function(event) {
              mention_member(event.data.member_id);
            });
            if (member.color) {
              $( "#discorduser-" + member.id.toString() + "d").css("color", "#" + member.color);
            }
          }
        }
        $("#discord-members-count").html(discordmembercnt);
    }

    function fill_authenticated_users(users) {
        var template = $('#mustache_authedusers').html();
        Mustache.parse(template);
        $("#embed-discord-members").empty();
        $("#embed-discord-members-count").html(users.length);
        for (var i = 0; i < users.length; i++) {
            var member = users[i];
            var rendered = Mustache.render(template, {"id": member.id.toString() + "a", "username": member.username, "avatar": member.avatar_url});
            $("#embed-discord-members").append(rendered);
            $( "#discorduser-" + member.id.toString() + "a").click({"member_id": member.id.toString()}, function(event) {
              mention_member(event.data.member_id);
            });
        }
    }

    function fill_unauthenticated_users(users) {
        var template = $('#mustache_unauthedusers').html();
        Mustache.parse(template);
        $("#embed-unauth-users").empty();
        $("#guest-members-count").html(users.length);
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
            priority_query_guild = true;
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
            message.content = message.content.replace("<@&" + guild_id + ">", "@everyone");
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
        message.formatted_time = mome.format("h:mm A");
        return message;
    }

    function parse_message_attachments(message) {
        for (var i = 0; i < message.attachments.length; i++) {
            var attach = "";
            if (message.content.length != 0) {
                attach = " ";
            }
            attach += message.attachments[i].url;
            message.content += attach;
        }
        return message;
    }

    function handle_last_message_mention() {
        var lastmsg = $("#chatcontent p:last-child");
        var content = lastmsg.text().toLowerCase();
        var username_discrim = $("#currentusername").text().toLowerCase();
        if (content.includes("@everyone") || content.includes("@" + username_discrim)) {
            lastmsg.css( "color", "#ff5252" );
            lastmsg.css( "font-weight", "bold" );
        }
    }

    function escapeHtml(unsafe) { /* http://stackoverflow.com/questions/6234773/can-i-escape-html-special-chars-in-javascript */
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
     }

    function nl2br (str, is_xhtml) {   /* http://stackoverflow.com/questions/2919337/jquery-convert-line-breaks-to-br-nl2br-equivalent/ */
        var breakTag = (is_xhtml || typeof is_xhtml === 'undefined') ? '<br />' : '<br>';
        return (str + '').replace(/([^>\r\n]?)(\r\n|\n\r|\r|\n)/g, '$1'+ breakTag +'$2');
    }

    function parse_channels_in_message(message) {
        var channelids = Object.keys(guild_channels);
        for (var i = 0; i < channelids.length; i++) {
            var pattern = "<#" + channelids[i] + ">";
            message.content = message.content.replace(new RegExp(pattern, "g"), "#" + guild_channels[channelids[i]].channel.name);
        }
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
            message = parse_message_attachments(message);
            message = parse_channels_in_message(message);
            var rendered = Mustache.render(template, {"id": message.id, "full_timestamp": message.formatted_timestamp, "time": message.formatted_time, "username": message.author.username, "discriminator": message.author.discriminator, "content": nl2br(escapeHtml(message.content))});
            $("#chatcontent").append(rendered);
            last = message.id;
            handle_last_message_mention();
        }
        $("html, body").animate({ scrollTop: $(document).height() }, "slow");
        $('#chatcontent').linkify({
            target: "_blank"
        });
        return last;
    }

    function run_fetch_routine() {
        if (currently_fetching) {
            return;
        }
        currently_fetching = true;
        times_fetched += 1;
        var channel_id = selected_channel;
        var fet;
        var jumpscroll;
        $("#fetching-indicator").fadeIn(800);
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
            update_embed_userchip(status.authenticated, status.avatar, status.username, status.user_id, status.discriminator);
            last_message_id = fill_discord_messages(data.messages, jumpscroll);
            if (status.manage_embed) {
                $("#administrate_link").show();
            } else {
                $("#administrate_link").hide();
            }
            if (times_fetched % 10 == 0 || priority_query_guild) {
              var guild = query_guild();
              guild.done(function(guildobj) {
                  priority_query_guild = false;
                  fill_channels(guildobj.channels);
                  fill_discord_members(guildobj.discordmembers);
                  fill_authenticated_users(guildobj.embedmembers.authenticated);
                  fill_unauthenticated_users(guildobj.embedmembers.unauthenticated);
                  fetchtimeout = setTimeout(run_fetch_routine, 5000);
              });
            } else {
              fetchtimeout = setTimeout(run_fetch_routine, 5000);
            }
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
          if (500 <= data.status && data.status < 600) {
              if (fetch_error_count % 5 == 0) {
                  Materialize.toast('Fetching messages error! EndenDragon probably broke something. Sorry =(', 10000);
              }
              fetch_error_count += 1;
              fetchtimeout = setTimeout(run_fetch_routine, 10000);
          }
        });
        fet.always(function() {
            currently_fetching = false;
            $("#fetching-indicator").fadeOut(800);
        });
    }

    function update_embed_userchip(authenticated, avatar, username, userid, discrim=null) {
        if (authenticated) {
            $("#currentuserimage").show();
            $("#currentuserimage").attr("src", avatar);
            $("#currentusername").text(username + "#" + discrim);
        } else {
            $("#currentuserimage").hide();
            $("#currentusername").text(username + "#" + userid);
        }
    }

    $("#discordlogin_btn").click(function() {
        lock_login_fields();
        wait_for_discord_login();
    });

    $("#custom_username_field").keyup(function(event){
        if (event.keyCode == 13) {
            if (!(new RegExp(/^[a-z\d\-_\s]+$/i).test($(this).val()))) {
                Materialize.toast('Illegal username provided! Only alphanumeric, spaces, dashes, and underscores allowed in usernames.', 10000);
                return;
            }
            if($(this).val().length >= 2 && $(this).val().length <= 32) {
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
                    } else if (data.status == 406) {
                        Materialize.toast('Illegal username provided! Only alphanumeric, spaces, dashes, and underscores allowed in usernames.', 10000);
                    }
                    unlock_login_fields();
                });
            }
        }
    });

    $("#messagebox").keyup(function(event){
        if ($(this).val().length == 1) {
            $(this).val($.trim($(this).val()));
        }
        if(event.keyCode == 13 && $(this).val().length >= 1 && $(this).val().length <= 350) {
            $(this).val($.trim($(this).val()));
            $(this).blur();
            $("#messagebox").attr('readonly', true);
            var funct = post(selected_channel, $(this).val());
            funct.done(function(data) {
                $("#messagebox").val("");
                clearTimeout(fetchtimeout);
                run_fetch_routine();
            });
            funct.fail(function(data) {
                Materialize.toast('Failed to send message.', 10000);
                if (data.responseJSON) {
                    for (var i = 0; i < data.responseJSON.illegal_reasons.length; i++) {
                        Materialize.toast(data.responseJSON.illegal_reasons[i], 10000);
                    }
                }
            });
            funct.catch(function(data) {
                if (data.status == 429) {
                    Materialize.toast('You are sending messages too fast! 1 message per 10 seconds', 10000);
                }
            });
            funct.always(function() {
                $("#messagebox").attr('readonly', false);
            });
        }
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
})();
