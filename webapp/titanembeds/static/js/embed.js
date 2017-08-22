/* global $ */
/* global Materialize */
/* global Mustache */
/* global guild_id */
/* global bot_client_id */
/* global moment */
/* global localStorage */
/* global visitors_enabled */
/* global cheet */
/* global location */
/* global io */

(function () {
    const theme_options = ["DiscordDark", "BetterTitan"]; // All the avaliable theming names
    
    var user_def_css; // Saves the user defined css
    var has_already_been_focused = false; // keep track of if the embed has initially been focused.
    var has_already_been_initially_resized = false; // keep track if the embed initially been resized
    var logintimer; // timer to keep track of user inactivity after hitting login
    var last_message_id; // last message tracked
    var selected_channel = null; // user selected channel
    var guild_channels = {}; // all server channels used to highlight channels in messages
    var emoji_store = []; // all server emojis
    var current_username_discrim; // Current username/discrim pair, eg EndenDraogn#4151
    var visitor_mode = false; // Keep track of if using the visitor mode or authenticate mode
    var socket = null; // Socket.io object
    var authenticated_users_list = []; // List of all authenticated users
    var unauthenticated_users_list = []; // List of all guest users
    var discord_users_list = []; // List of all discord users that are probably online

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
    
    String.prototype.replaceAll = function(target, replacement) {
        return this.split(target).join(replacement);
    };

    function query_guild() {
        var url = "/api/query_guild";
        if (visitor_mode) {
            url = url += "_visitor";
        }
        var funct = $.ajax({
            dataType: "json",
            url: url,
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
    
    function change_unauthenticated_username(username) {
        var funct = $.ajax({
            method: "POST",
            dataType: "json",
            url: "/api/change_unauthenticated_username",
            data: {"username": username, "guild_id": guild_id}
        });
        return funct.promise();
    }

    function fetch(channel_id, after=null) {
        var url = "/api/fetch";
        if (visitor_mode) {
            url += "_visitor";
        }
        var funct = $.ajax({
            method: "GET",
            dataType: "json",
            url: url,
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
    
    function discord_embed() {
        var funct = $.ajax({
            dataType: "json",
            url: "https://discordapp.com/api/guilds/" + guild_id + "/widget.json",
        });
        return funct.promise();
    }
    
    $(function() {
        if ($("#user-defined-css").length > 0) {
            user_def_css = $("#user-defined-css").text();
        }
        
        $('select').material_select();
        
        $("#loginmodal").modal({
            dismissible: visitors_enabled, // Modal can be dismissed by clicking outside of the modal
            opacity: .5, // Opacity of modal background
            inDuration: 300, // Transition in duration
            outDuration: 200, // Transition out duration
            startingTop: '4%', // Starting top style attribute
            endingTop: '10%', // Ending top style attribute
          }
        );
        $('#loginmodal').modal('open');
        
        $("#focusmodal").modal({
            dismissible: true,
            opacity: .5,
            inDuration: 400,
            outDuration: 400,
            startingTop: "4%",
            endingTop: "10%",
        });
        $("#focusmodal").modal("open");
        $("#userembedmodal").modal({
            dismissible: true,
            opacity: .5,
            inDuration: 400,
            outDuration: 400,
        });
        
        $("#nameplate").click(function () {
            $("#userembedmodal").modal("open");
        });
        
        $("#visitor_login_btn").click(function () {
            $("#loginmodal").modal("open");
        });
        
        $("#emoji-tray-toggle").click(function () {
            $("#emoji-picker").fadeToggle();
            var offset = $("#emoji-tray-toggle").offset().top;
            $("#emoji-picker").offset({"top": offset-120});
            $("#emoji-picker-emojis").html("");
            var template = $('#mustache_message_emoji').html();
            Mustache.parse(template);
            for (var i = 0; i < emoji_store.length; i++) {
                var emoji = emoji_store[i];
                var rendered = Mustache.render(template, {"id": emoji.id, "name": emoji.name}).trim();
                var jqueryed = $(rendered);
                jqueryed.click(function () {
                    var emote_name = $(this).attr("data-tooltip");
                    place_emoji(emote_name);
                });
                $("#emoji-picker-emojis").append(jqueryed);
            }
            $('.tooltipped').tooltip();
        });
        
        $("#chatcontent").click(function () {
            var emojipck_display = $('#emoji-picker').css('display');
            if (emojipck_display != "none") {
                $("#emoji-picker").fadeToggle();
            }
        });

        $("#messagebox").click(function () {
            var emojipck_display = $('#emoji-picker').css('display');
            if (emojipck_display != "none") {
                $("#emoji-picker").fadeToggle();
            }
        });
        
        $( "#theme-selector" ).change(function () {
            var theme = $("#theme-selector option:selected").val();
            var keep_custom_css = $("#overwrite_theme_custom_css_checkbox").is(':checked');
            changeTheme(theme, keep_custom_css);
        });
        
        $("#overwrite_theme_custom_css_checkbox").change(function () {
            var keep_custom_css = $("#overwrite_theme_custom_css_checkbox").is(':checked');
            changeTheme(null, keep_custom_css);
        });
        
        var themeparam = getParameterByName('theme');
        var localstore_theme = localStorage.getItem("theme");
        if ((themeparam && $.inArray(themeparam, theme_options) != -1) || (localstore_theme)) {
            var theme;
            if (themeparam) {
                theme = themeparam;
            } else {
                theme = localstore_theme;
            }
            changeTheme(theme);
            $("#theme-selector option").removeAttr('selected');
            $("#theme-selector option[value=" + theme + "]").attr('selected', 'selected');
            $('select').material_select();
        }
        
        var dembed = discord_embed();
        dembed.done(function (data) {
            $("#modal_invite_btn").attr("href", data.instant_invite);
        });
        
        $(window).resize(function(){
            // For those who decides to hide the embed at first load (display: none), resulting in the messages being not scrolled down.
            if (!has_already_been_initially_resized) {
                has_already_been_initially_resized = true;
                $("html, body").animate({ scrollTop: $(document).height() }, "fast");
            }
        });
        
        if (getParameterByName("forcefocus") == "1") {
            if (document.hasFocus()) {
                primeEmbed();
            }
            
            $(window).focus(function() {
                if (!has_already_been_focused) {
                    primeEmbed();
                }
            });
        } else {
            primeEmbed();
        }
        
        setInterval(send_socket_heartbeat, 5000);
    });
    
    function changeTheme(theme=null, keep_custom_css=true) {
        if (theme == "") {
          $("#css-theme").attr("href", "");
          $("#user-defined-css").text(user_def_css);
          localStorage.removeItem("theme");
        } else if ($.inArray(theme, theme_options) != -1 || theme == null) {
            if (!keep_custom_css) {
                $("#user-defined-css").text("");
            } else {
                $("#user-defined-css").text(user_def_css);
            }
            if (theme) {
                $("#css-theme").attr("href", "/static/themes/" + theme + "/css/style.css");
                localStorage.setItem("theme", theme);
            }
        }
    }
    
    /* https://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript */
    function getParameterByName(name, url) {
        if (!url) url = window.location.href;
        name = name.replace(/[\[\]]/g, "\\$&");
        var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
            results = regex.exec(url);
        if (!results) return null;
        if (!results[2]) return '';
        return decodeURIComponent(results[2].replace(/\+/g, " "));
    }
    
    function setVisitorMode(enabled) {
        if (!visitors_enabled) {
            return;
        }
        visitor_mode = enabled;
        if (visitor_mode) {
            $("#visitor_mode_message").show();
            $("#messagebox").hide();
            $("#emoji-tray-toggle").hide();
        } else {
            $("#visitor_mode_message").hide();
            $("#messagebox").show();
            $("#emoji-tray-toggle").show();
        }
    }

    function primeEmbed() {
        $("#focusmodal").modal("close");
        has_already_been_focused = true;
        
        lock_login_fields();

        var guild = query_guild();
        guild.fail(function() {
            unlock_login_fields();
            if (visitors_enabled) {
                setVisitorMode(true);
                var guild2 = query_guild();
                guild2.done(function(data) {
                    initialize_embed(data);
                });
                guild2.fail(function() {
                    setVisitorMode(false);
                });
            }
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
        if (socket) {
            socket.disconnect();
        }
        if (guildobj === undefined) {
            var guild = query_guild();
            guild.done(function(data) {
                switch_to_default_channel(data.channels);
                prepare_guild(data);
                $('#loginmodal').modal('close');
                unlock_login_fields();
            });
        } else {
            switch_to_default_channel(guildobj.channels);
            prepare_guild(guildobj);
            $('#loginmodal').modal('close');
            unlock_login_fields();
        }
    }
    
    function switch_to_default_channel(guildchannels) {
        var defaultChannel = getParameterByName("defaultchannel");
        if (!defaultChannel) {
            return;
        }
        for (var i = 0; i < guildchannels.length; i++) {
            if (guildchannels[i].channel.id == defaultChannel) {
                if (!guildchannels[i].read) {
                    return;
                }
                selected_channel = defaultChannel;
                return;
            }
        }
    }

    function prepare_guild(guildobj) {
        emoji_store = guildobj.emojis;
        fill_channels(guildobj.channels);
        fill_discord_members(guildobj.discordmembers);
        fill_authenticated_users(guildobj.embedmembers.authenticated);
        fill_unauthenticated_users(guildobj.embedmembers.unauthenticated);
        $("#instant-inv").attr("href", guildobj.instant_invite);
        run_fetch_routine();
        initiate_websockets();
    }

    function fill_channels(channels) {
        var template = $('#mustache_channellistings').html();
        Mustache.parse(template);
        $("#channels-list").empty();
        var curr_default_channel = selected_channel;
        for (var i = 0; i < channels.length; i++) {
            var chan = channels[i];
            guild_channels[chan.channel.id] = chan;
            if (chan.read) {
              var rendered = Mustache.render(template, {"channelid": chan.channel.id, "channelname": chan.channel.name});
              $("#channels-list").append(rendered);
              $("#channel-" + chan.channel.id.toString()).click({"channel_id": chan.channel.id.toString()}, function(event) {
                  select_channel(event.data.channel_id);
              });
              if (!selected_channel && (!curr_default_channel || chan.channel.position < curr_default_channel.channel.position)) {
                  curr_default_channel = chan;
              }
            }
        }
        if (typeof curr_default_channel == "object") {
            selected_channel = curr_default_channel.channel.id;
        }
        var this_channel = guild_channels[selected_channel];
        if (this_channel.write) {
            $("#messagebox").prop('disabled', false);
            $("#messagebox").prop('placeholder', "Enter message");
        } else {
            $("#messagebox").prop('disabled', true);
            $("#messagebox").prop('placeholder', "Messages is disabled in this channel.");
        }
        $("#channeltopic").text(this_channel.channel.topic);
        $("#channel-"+selected_channel).parent().addClass("active");
    }

    function mention_member(member_id) {
      if (!$('#messagebox').prop('disabled')) {
        $('#messagebox').val( $('#messagebox').val() + "[@" + member_id + "] " );
        $('.button-collapse').sideNav('hide');
        $("#messagebox").focus();
      }
    }
    
    function place_emoji(emoji_name) {
        if (!$('#messagebox').prop('disabled')) {
            $('#messagebox').val( $('#messagebox').val() + emoji_name + " " );
            $("#messagebox").focus();
        }
        var emojipck_display = $('#emoji-picker').css('display');
        if (emojipck_display != "none") {
            $("#emoji-picker").fadeToggle();
        }
    }

    function fill_discord_members(discordmembers) {
        discord_users_list = discordmembers;
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
          roleobj.members.sort(function(a, b){
              var name_a = a.username;
              var name_b = b.username;
              if (a.nick) {
                  name_a = a.nick;
              }
              if (b.nick) {
                  name_b = b.nick;
              }
              name_a = name_a.toUpperCase();
              name_b = name_b.toUpperCase();
              if(name_a < name_b) return -1;
              if(name_a > name_b) return 1;
              return 0;
            });
          for (var j = 0; j < roleobj.members.length; j++) {
            var member = roleobj.members[j];
            var member_name = member.nick;
            if (!member_name) {
                member_name = member.username;
            }
            var rendered_user = Mustache.render(template_user, {"id": member.id.toString() + "d", "username": member_name, "avatar": member.avatar_url});
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
            var username = member.username;
            if (member.nickname) {
                username = member.nickname;
            }
            var rendered = Mustache.render(template, {"id": member.id.toString() + "a", "username": username, "avatar": member.avatar_url});
            $("#embed-discord-members").append(rendered);
            $( "#discorduser-" + member.id.toString() + "a").click({"member_id": member.id.toString()}, function(event) {
              mention_member(event.data.member_id);
            });
        }
        authenticated_users_list = users;
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
        unauthenticated_users_list = users;
    }

    function wait_for_discord_login() {
        _wait_for_discord_login(0);
    }

    function _wait_for_discord_login(index) {
        setTimeout(function() {
            var usr = create_authenticated_user();
            usr.done(function(data) {
                setVisitorMode(false);
                initialize_embed();
                return;
            });
            usr.fail(function(data) {
                if (data.status == 403) {
                    Materialize.toast('Authentication error! You have been banned.', 10000);
                    setVisitorMode(true);
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
            run_fetch_routine();
        }
    }

    function replace_message_mentions(message) {
        var mentions = message.mentions;
        for (var i = 0; i < mentions.length; i++) {
            var mention = mentions[i];
            var username = mention.username;
            if (mention.nickname) {
                username = mention.nickname;
            }
            message.content = message.content.replace(new RegExp("<@" + mention.id + ">", 'g'), "@" + username + "#" + mention.discriminator);
            message.content = message.content.replace(new RegExp("<@!" + mention.id + ">", 'g'), "@" + username + "#" + mention.discriminator);
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
            if (message.content.startsWith("(Titan Dev) ")) {
                message.content = message.content.substring(usernamefield.length + 18);
            } else {
                message.content = message.content.substring(usernamefield.length + 7);
            }
            message.author.username = usernamefield.split("#")[0];
            message.author.discriminator = usernamefield.split("#")[1];
        } else if (message.author.bot && message.author.discriminator == "0000" && message.author.username.substring(message.author.username.length-5, message.author.username.length-4) == "#") {
            var namestr = message.author.username;
            if (message.content.startsWith("(Titan Dev) ")) {
                message.author.username = "(Titan Dev) " + namestr.substring(0,namestr.length-5);
                message.content = message.content.substring(11);
            } else {
                message.author.username = namestr.substring(0,namestr.length-5);
            }
            message.author.discriminator = namestr.substring(namestr.length-4);
        }
        return message;
    }

    function parse_message_time(message) {
        var mome = moment(message.timestamp);
        message.formatted_timestamp = mome.toDate().toString();
        message.formatted_time = mome.calendar();
        /*message.formatted_time = mome.format("h:mm A");*/
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
        var username_discrim = current_username_discrim.toLowerCase();
        if (content.includes("@everyone") || content.includes("@here") || content.includes("@" + username_discrim)) {
            lastmsg.addClass( "mentioned" );
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
    
    function parse_emoji_in_message(message) {
        var template = $('#mustache_message_emoji').html();
        Mustache.parse(template);
        for (var i = 0; i < emoji_store.length; i++) {
            var emoji = emoji_store[i];
            var emoji_format = "&lt;:" + emoji.name + ":" + emoji.id + "&gt;";
            var rendered = Mustache.render(template, {"id": emoji.id, "name": emoji.name}).trim();
            message.content = message.content.replaceAll(emoji_format, rendered);
        }
        return message;
    }
    
    function parse_message_markdown(text) {
        text = text.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");
        text = text.replace(/\*(.*?)\*/g, "<i>$1</i>");
        text = text.replace(/__(.*?)__/g, "<u>$1</u>");
        text = text.replace(/_(.*?)_/g, "<i>$1</i>");
        text = text.replace(/~~(.*?)~~/g, "<del>$1</del>");
        text = text.replace(/\`\`\`([^]+)\`\`\`/g, "<code class=\"blockcode\">$1</code>");
        text = text.replace(/\`(.*?)\`/g, "<code>$1</code>");
        return text;
    }

    function fill_discord_messages(messages, jumpscroll, replace=null) {
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
            message.content = escapeHtml(message.content);
            message.content = parse_message_markdown(message.content);
            message = parse_emoji_in_message(message);
            var username = message.author.username;
            if (message.author.nickname) {
                username = message.author.nickname;
            }
            var rendered = Mustache.render(template, {"id": message.id, "full_timestamp": message.formatted_timestamp, "time": message.formatted_time, "username": username, "discriminator": message.author.discriminator, "content": nl2br(message.content)});
            if (replace == null) {
                $("#chatcontent").append(rendered);
                handle_last_message_mention();
                $("#chatcontent p:last-child").find(".blockcode").find("br").remove(); // Remove excessive breaks in codeblocks
            } else {
                replace.html($(rendered).html());
                replace.find(".blockcode").find("br").remove();
            }
            last = message.id;
        }
        if (replace == null) {
            $("html, body").animate({ scrollTop: $(document).height() }, "slow");
        }
        $('#chatcontent').linkify({
            target: "_blank"
        });
        $('.tooltipped').tooltip();
        return last;
    }

    function run_fetch_routine() {
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
            if (visitor_mode) {
                update_embed_userchip(false, null, "Titan", null, "0001", null);
                update_change_username_modal();
            } else {
                update_embed_userchip(status.authenticated, status.avatar, status.username, status.nickname, status.user_id, status.discriminator);
                update_change_username_modal(status.authenticated, status.username);
            }
            last_message_id = fill_discord_messages(data.messages, jumpscroll);
            if (!visitor_mode && status.manage_embed) {
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
                $("#instant-inv").attr("href", guildobj.instant_invite);
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
            setVisitorMode(true);
        });
        fet.always(function() {
            $("#fetching-indicator").fadeOut(800);
        });
    }

    function update_embed_userchip(authenticated, avatar, username, nickname, userid, discrim=null) {
        if (authenticated) {
            $("#currentuserimage").show();
            $("#currentuserimage").attr("src", avatar);
            $("#curuser_name").text(username);
            $("#curuser_discrim").text("#" + discrim);
            current_username_discrim = "#" + discrim;
        } else {
            $("#currentuserimage").hide();
            $("#curuser_name").text(username);
            $("#curuser_discrim").text("#" + userid);
            current_username_discrim = "#" + userid;
        }
        if (nickname) {
            $("#curuser_name").text(nickname);
            current_username_discrim = nickname + current_username_discrim;
        } else {
            current_username_discrim = username + current_username_discrim;
        }
    }
    
    function update_change_username_modal(authenticated=false, username=null) {
        if (!$("#change_username_field") || $("#change_username_field").is(":focus")) {
            return;
        }
        if (authenticated || visitor_mode) {
            $("#change_username_field").attr("disabled", true);
            $("#change_username_field").val("");
        } else {
            $("#change_username_field").attr("disabled", false);
            $("#change_username_field").val(username);
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
                    setVisitorMode(false);
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
                    setVisitorMode(true);
                });
            }
        }
    });
    
    $("#change_username_field").keyup(function(event){
        if (event.keyCode == 13) {
            $(this).blur();
            if (!(new RegExp(/^[a-z\d\-_\s]+$/i).test($(this).val()))) {
                Materialize.toast('Illegal username provided! Only alphanumeric, spaces, dashes, and underscores allowed in usernames.', 10000);
                return;
            }
            if(($(this).val().length >= 2 && $(this).val().length <= 32) && $("#curuser_name").text() != $(this).val()) {
                var usr = change_unauthenticated_username($(this).val());
                usr.done(function(data) {
                    Materialize.toast('Username changed successfully!', 10000);
                    run_fetch_routine();
                });
                usr.fail(function(data) {
                    if (data.status == 429) {
                        Materialize.toast('Sorry! You are allowed to change your username once every 15 minutes.', 10000);
                    } else if (data.status == 403) {
                        Materialize.toast('Authentication error! You have been banned.', 10000);
                    } else if (data.status == 406) {
                        Materialize.toast('Illegal username provided! Only alphanumeric, spaces, dashes, and underscores allowed in usernames.', 10000);
                    } else {
                        Materialize.toast('Something unexpected happened! Error code of ' + data.status, 10000);
                    }
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
                $("#messagebox").focus();
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
    
    // enter konami code into the embed page for some ponies action!
    cheet('↑ ↑ ↓ ↓ ← → ← → b a', function () {
        // basically copied and pasted of browser ponies bookmarklet
        (function (srcs,cfg) { var cbcount = 1; var callback = function () { -- cbcount; if (cbcount === 0) { BrowserPonies.setBaseUrl(cfg.baseurl); if (!BrowserPoniesBaseConfig.loaded) { BrowserPonies.loadConfig(BrowserPoniesBaseConfig); BrowserPoniesBaseConfig.loaded = true; } BrowserPonies.loadConfig(cfg); if (!BrowserPonies.running()) BrowserPonies.start(); } }; if (typeof(BrowserPoniesConfig) === "undefined") { window.BrowserPoniesConfig = {}; } if (typeof(BrowserPoniesBaseConfig) === "undefined") { ++ cbcount; BrowserPoniesConfig.onbasecfg = callback; } if (typeof(BrowserPonies) === "undefined") { ++ cbcount; BrowserPoniesConfig.oninit = callback; } var node = (document.body || document.documentElement || document.getElementsByTagName('head')[0]); for (var id in srcs) { if (document.getElementById(id)) continue; if (node) { var s = document.createElement('script'); s.type = 'text/javascript'; s.id = id; s.src = srcs[id]; node.appendChild(s); } else { document.write('\u003cscript type="text/javscript" src="'+ srcs[id]+'" id="'+id+'"\u003e\u003c/script\u003e'); } } callback();})({"browser-ponies-script":"https://panzi.github.io/Browser-Ponies/browserponies.js","browser-ponies-config":"https://panzi.github.io/Browser-Ponies/basecfg.js"},{"baseurl":"https://panzi.github.io/Browser-Ponies/","fadeDuration":500,"volume":1,"fps":25,"speed":3,"audioEnabled":false,"showFps":false,"showLoadProgress":true,"speakProbability":0.1,"spawn":{"applejack":1,"fluttershy":1,"pinkie pie":1,"rainbow dash":1,"rarity":1,"twilight sparkle":1}});
    });
    
    function initiate_websockets() {
        if (socket) {
            return;
        }
        
        socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + "/gateway", {path: '/gateway', transports: ['websocket']});
        socket.on('connect', function () {
            socket.emit('identify', {"guild_id": guild_id, "visitor_mode": visitor_mode});
        });
        
        socket.on("disconnect", function () {
            socket = null;
        });
        
        socket.on("revoke", function () {
            $('#loginmodal').modal('open');
            setVisitorMode(true);
            primeEmbed();
            Materialize.toast('Authentication error! You have been disconnected by the server.', 10000);
        });
        
        socket.on("embed_user_connect", function (msg) {
            if (msg.unauthenticated) {
                for (var i = 0; i < unauthenticated_users_list.length; i++) {
                    var item = unauthenticated_users_list[i];
                    if (item.username == msg.username && item.discriminator == msg.discriminator) {
                        return;
                    }
                }
                unauthenticated_users_list.push(msg);
                fill_unauthenticated_users(unauthenticated_users_list);
            } else {
                for (var i = 0; i < authenticated_users_list.length; i++) {
                    var item = authenticated_users_list[i];
                    if (item.id == msg.id) {
                        return;
                    }
                }
                authenticated_users_list.push(msg);
                fill_authenticated_users(authenticated_users_list);
            }
        });
        
        socket.on("embed_user_disconnect", function (msg) {
            if (msg.unauthenticated) {
                for (var i = 0; i < unauthenticated_users_list.length; i++) {
                    var item = unauthenticated_users_list[i];
                    if (item.username == msg.username && item.discriminator == msg.discriminator) {
                        unauthenticated_users_list.splice(i, 1);
                        fill_unauthenticated_users(unauthenticated_users_list);
                        return;
                    }
                }
            } else {
                for (var i = 0; i < authenticated_users_list.length; i++) {
                    var item = authenticated_users_list[i];
                    if (item.id == msg.id) {
                        authenticated_users_list.splice(i, 1);
                        fill_authenticated_users(authenticated_users_list);
                        return;
                    }
                }
            }
        });
        
        socket.on("MESSAGE_CREATE", function (msg) {
            var thismsgchan = msg.channel_id;
            if (selected_channel != thismsgchan) {
                return;
            }
            var jumpscroll = element_in_view($('#discordmessage_'+last_message_id), true);
            last_message_id = fill_discord_messages([msg], jumpscroll);
        });
        
        socket.on("MESSAGE_DELETE", function (msg) {
            var msgchan = msg.channel_id;
            if (selected_channel != msgchan) {
                return;
            }
            $("#discordmessage_"+msg.id).parent().remove();
            last_message_id = $("#chatcontent").find("[id^=discordmessage_]").last().attr('id').substring(15);
        });
        
        socket.on("MESSAGE_UPDATE", function (msg) {
            var msgelem = $("#discordmessage_"+msg.id);
            if (msgelem.length == 0) {
                return;
            }
            var msgelem_parent = msgelem.parent();
            fill_discord_messages([msg], false, msgelem_parent);
        });
        
        socket.on("GUILD_MEMBER_ADD", function (usr) {
            if (usr.status != "offline") {
                discord_users_list.push(usr);
                fill_discord_members(discord_users_list);
            }
        });
        
        socket.on("GUILD_MEMBER_UPDATE", function (usr) {
            for (var i = 0; i < discord_users_list.length; i++) {
                if (usr.id == discord_users_list[i].id) {
                    discord_users_list.splice(i, 1);
                    if (usr.status != "offline") {
                        discord_users_list.push(usr);
                    }
                    fill_discord_members(discord_users_list);
                    return;
                }
            }
            discord_users_list.push(usr);
            fill_discord_members(discord_users_list);
        });

        socket.on("GUILD_MEMBER_REMOVE", function (usr) {
            for (var i = 0; i < discord_users_list.length; i++) {
                if (usr.id == discord_users_list[i].id) {
                    discord_users_list.splice(i, 1);
                    fill_discord_members(discord_users_list);
                    return;
                }
            }
        });

        socket.on("GUILD_EMOJIS_UPDATE", function (emo) {
            emoji_store = emo;
        });
    }
    
    function send_socket_heartbeat() {
        if (!socket) {
            return;
        }
        socket.emit("heartbeat", {"guild_id": guild_id, "visitor_mode": visitor_mode});
    }
})();
