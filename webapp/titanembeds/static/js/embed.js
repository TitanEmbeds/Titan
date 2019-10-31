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
/* global twemoji */
/* global jQuery */
/* global grecaptcha */
/* global hljs */
/* global linkify */
/* global unauth_captcha_enabled */
/* global soundManager */
/* global disabled */
/* global wdtEmojiBundle */
/* global EmojiConvertor */
/* global post_timeout */
/* global is_peak */
/* global cookie_test_s2_URL */

(function () {
    const theme_options = ["DiscordDark", "FireWyvern", "IceWyvern", "MetroEdge", "BetterTitan"]; // All the avaliable theming names
    const badges_options = ["administrator", "partner", "supporter", "discordbotsorgvoted"]; // All badges avaliable
    
    var user_def_css; // Saves the user defined css
    var has_already_been_initially_resized = false; // keep track if the embed initially been resized
    var has_handled_noscroll = false; // Prevent scrolling to bottom of embed at load if false
    var logintimer; // timer to keep track of user inactivity after hitting login
    var last_message_id; // last message tracked
    var selected_channel = null; // user selected channel
    var guild_channels = {}; // all server channels used to highlight channels in messages
    var emoji_store = []; // all server emojis
    var current_username_discrim; // Current username/discrim pair, eg EndenDraogn#4151
    var current_user_discord_id; // Current user discord snowflake id, eg mine is 140252024666062848
    var visitor_mode = false; // Keep track of if using the visitor mode or authenticate mode
    var socket = null; // Socket.io object
    var socket_last_ack = null; // Socket.io last acknowledgement Moment obj
    var socket_error_should_refetch = false; // If true, the next ack will trigger a http refetch if socket connected
    var socket_identified = false; // identified/loggedin with socket
    var authenticated_users_list = []; // List of all authenticated users
    var unauthenticated_users_list = []; // List of all guest users
    var discord_users_list = []; // List of all discord users that are probably online
    var guild_channels_list = []; // guild channels, but as a list of them
    var message_users_cache = {}; // {"name#discrim": {"data": {}, "msgs": []} Cache of the users fetched from websockets to paint the messages
    var shift_pressed = false; // Track down if shift pressed on messagebox
    var global_guest_icon = null; // Guest icon
    var notification_sound = null; // Sound Manager 2 demonstrative.mp3 object https://notificationsounds.com/message-tones/demonstrative-516
    var notification_sound_setting; // nothing, mentions, newmsgs - to control what new sound it makes
    var display_richembeds; // true/false - if rich embeds should be displayed
    var guild_roles_list = []; // List of all guild roles
    var all_users = []; // List of all the users in guild
    var is_dragging_chatcontainer = false; // Track if is dragging on chatcontainer (does not trigger messagebox focus) or not
    var localstorage_avaliable = false; // Check if localstorage is avaliable on this browser
    var shouldUtilizeGateway = false; // Don't connect to gateway until page is focused or has interaction.
    var discord_users_list_enabled = false; // Allow automatic population of discord users list

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
    
    // https://stackoverflow.com/questions/2956966/javascript-telling-setinterval-to-only-fire-x-amount-of-times
    function setIntervalX(callback, delay, repetitions) {
        var x = 0;
        var intervalID = window.setInterval(function () {
    
           callback();
    
           if (++x === repetitions) {
               window.clearInterval(intervalID);
           }
        }, delay);
    }
    
    String.prototype.replaceAll = function(target, replacement) {
        return this.split(target).join(replacement);
    };
    
    function zeroPad(discrim) {
        var str = "" + discrim;
        var pad = "0000";
        return pad.substring(0, pad.length - str.length) + str;
    }

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

    function create_unauthenticated_user(username, captchaResponse) {
        var funct = $.ajax({
            method: "POST",
            dataType: "json",
            url: "/api/create_unauthenticated_user",
            data: {"username": username, "guild_id": guild_id, "captcha_response": captchaResponse}
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

    function fetch(channel_id, after) {
        if (after === undefined) {
            after = null;
        }
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

    function post(channel_id, content, file) {
        if (content == "") {
            content = null;
        }
        var data = null;
        var ajaxobj = {
            method: "POST",
            dataType: "json",
            url: "/api/post"
        }
        if (file) {
            data = new FormData();
            data.append("guild_id", guild_id);
            data.append("channel_id", channel_id);
            if (content) {
                data.append("content", content);
            }
            data.append("file", file);
            ajaxobj.cache = false;
            ajaxobj.contentType = false;
            ajaxobj.processData = false;
            ajaxobj.xhr = function() {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    // For handling the progress of the upload
                    myXhr.upload.addEventListener('progress', function(e) {
                        if (e.lengthComputable) {
                            $("#filemodalprogress-inner").css("width", (e.loaded/e.total) * 100 + "%")
                        }
                    } , false);
                }
                return myXhr;
            }
        } else {
            data = {"guild_id": guild_id, "channel_id": channel_id, "content": content};
        }
        ajaxobj.data = data;
        var funct = $.ajax(ajaxobj);
        return funct.promise();
    }
    
    function discord_embed() {
        var funct = $.ajax({
            dataType: "json",
            url: "https://discordapp.com/api/guilds/" + guild_id + "/widget.json",
        });
        return funct.promise();
    }
    
    function api_user(user_id) {
        var funct = $.ajax({
            dataType: "json",
            url: "/api/user/" + guild_id + "/" + user_id,
        });
        return funct.promise();
    }
    
    function list_users() {
        var funct = $.ajax({
            dataType: "json",
            url: "/api/user/" + guild_id,
        });
        return funct.promise();
    }
    
    function server_members() {
        var url = "/api/server_members";
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
    
    function performLocalStorageTest() {
        var test = 'test';
        try {
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            localstorage_avaliable = true;
            return true;
        } catch(e) {
            localstorage_avaliable = false;
            return false;
        }
    }
    
    function enableGateway(event) {
        if (shouldUtilizeGateway) {
            return;
        }
        $(document).off("click focus", enableGateway);
        $("main").off("mousewheel", enableGateway);
        shouldUtilizeGateway = true;
        initiate_websockets();
    }
    
    function inIframe() {
        try {
            return window.self !== window.top;
        } catch (e) {
            return true;
        }
    }
    
    function isSameDomain() {
        try {
            return location.hostname == parent.location.hostname;
        } catch (e) {
            return false;
        }
    }
    
    $(function() {
        performLocalStorageTest();
        if ($("#user-defined-css").length > 0) {
            user_def_css = $("#user-defined-css").text();
        }
        
        // is not in iframe
        if ((!inIframe() || isSameDomain()) && !is_peak) {
            shouldUtilizeGateway = true;
        } else {
            if (is_peak) {
                $(document).on("click focus", enableGateway);
                $("main").on("mousewheel", enableGateway);
            } else {
                shouldUtilizeGateway = true;
            }
        }
        
        $("#upload-file-btn").hide();
        $("#send-msg-btn").hide();
        
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
        $("#recaptchamodal").modal({
            dismissible: true,
            opacity: .5,
            inDuration: 400,
            outDuration: 400,
            startingTop: '40%',
            endingTop: '30%',
        });
        $("#userembedmodal").modal({
            dismissible: true,
            opacity: .5,
            inDuration: 400,
            outDuration: 400,
        });
        $("#nsfwmodal").modal({
            dismissible: true,
            opacity: .3,
            inDuration: 400,
            outDuration: 400,
        });
        $("#filemodal").modal({
            dismissible: true,
            opacity: .3,
            inDuration: 400,
            outDuration: 400,
            complete: function () { $("#fileinput").val(""); }
        });
        $("#usercard").modal({
            opacity: .5,
        });
        
        $("#members-btn").click(function () {
            var sm = server_members();
            sm.done(function (data) {
                $("#members-spinner").hide();
                discord_users_list_enabled = data.widgetenabled;
                fill_discord_members(data.discordmembers);
                fill_authenticated_users(data.embedmembers.authenticated);
                fill_unauthenticated_users(data.embedmembers.unauthenticated);
            });
        });
        
        $("#nameplate").click(function () {
            $("#userembedmodal").modal("open");
        });
        
        $("#visitor_login_btn").click(function () {
            $("#loginmodal").modal("open");
        });
        
        $("#proceed_nsfw_btn").click(function () {
            var channel_id = $("#proceed_nsfw_btn").attr("channel_id");
            var should_animate = parseInt($("#proceed_nsfw_btn").attr("should_animate"));
            $("#nsfwmodal").modal("close");
            select_channel(channel_id, should_animate, true);
        });
        
        $("#dismiss_nsfw_btn").click(function () {
            $("#nsfwmodal").modal("close");
        });
        
        $("#upload-file-btn").click(function () {
            $("#fileinput").trigger('click');
        });
        
        $("#proceed_fileupload_btn").click(function () {
            $("#messagebox-filemodal").trigger(jQuery.Event("keydown", { keyCode: 13 } ));
        });
        
        $("#fileinput").change(function (e){
            var files = e.target.files;
            if (files && files.length > 0) {
                $("#messagebox-filemodal").val($("#messagebox").val());
                $("#filename").text($("#fileinput")[0].files[0].name);
                $("#filemodal").modal("open");
                $("#messagebox-filemodal").focus();
                var file = files[0];
                var file_size = file.size;
                var file_max_size = 4 * 1024 * 1024;
                if (file_size > file_max_size) {
                    $("#filemodal").modal("close");
                    Materialize.toast('Your file is too powerful! The maximum file size is 4 megabytes.', 5000);
                    return;
                }
                var name = file.name;
                var extension = name.substr(-4).toLowerCase();
                var image_extensions = [".png", ".jpg", ".jpeg", ".gif"];
                $("#filepreview").hide();
                if (FileReader && image_extensions.indexOf(extension) > -1) {
                    var reader = new FileReader();
                    reader.onload = function() {
                        $("#filepreview").show();
                        $("#filepreview")[0].src = reader.result;
                    };
                    reader.readAsDataURL(file);
                }
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
        
        hljs.configure({useBR: true});
        linkify.options.defaults.ignoreTags = ["code"];
        
        wdtEmojiBundle.defaults.emojiSheets = {
            'apple': 'https://cdnjs.cloudflare.com/ajax/libs/wdt-emoji-bundle/0.2.1/sheets/sheet_apple_64_indexed_128.png',
            'google': 'https://cdnjs.cloudflare.com/ajax/libs/wdt-emoji-bundle/0.2.1/sheets/sheet_google_64_indexed_128.png',
            'twitter': 'https://cdnjs.cloudflare.com/ajax/libs/wdt-emoji-bundle/0.2.1/sheets/sheet_twitter_64_indexed_128.png',
            'emojione': 'https://cdnjs.cloudflare.com/ajax/libs/wdt-emoji-bundle/0.2.1/sheets/sheet_emojione_64_indexed_128.png'
        };
        wdtEmojiBundle.defaults.pickerColors = ['gray'];
        wdtEmojiBundle.defaults.emojiType = 'twitter';
        wdtEmojiBundle.init('#messagebox');
        
        var themeparam = getParameterByName('theme');
        var localstore_theme = "";
        if (localstorage_avaliable) {
            localstore_theme = localStorage.getItem("theme");
        }
        if ((themeparam && $.inArray(themeparam, theme_options) != -1) || (localstore_theme)) {
            var theme;
            if (themeparam) {
                theme = themeparam;
            } else {
                theme = localstore_theme;
            }
            changeTheme(theme, true, false);
            $("#theme-selector option").removeAttr('selected');
            $("#theme-selector option[value=" + theme + "]").attr('selected', 'selected');
            $('select').material_select();
        }
        
        $("[name=notification_sound_radiobtn]").click(function (event) {
            changeNotificationSound(event.target.value);
        });
        var localstore_notification_sound = "";
        if (localstorage_avaliable) {
            localstore_notification_sound = localStorage.getItem("notification_sound");
        }
        if (localstore_notification_sound) {
            changeNotificationSound(localstore_notification_sound);
        } else {
            changeNotificationSound("mentions");
        }
        
        notification_sound = soundManager.createSound({
            id: 'notification_sound_id',
            url: "/static/audio/demonstrative.mp3",
            volume: 8,
        });
        
        $("[name=richembed_toggle_radiobtn]").click(function (event) {
            display_richembeds = event.target.value == "true";
            localStorage.setItem("display_richembeds", display_richembeds);
            $("[name=richembed_toggle_radiobtn][value=" + display_richembeds + "]").prop("checked", true);
        });
        var localstore_display_richembeds = "";
        if (localstorage_avaliable) {
            localstore_display_richembeds = localStorage.getItem("display_richembeds");
        }
        if (localstore_display_richembeds) {
            display_richembeds = !(localstore_display_richembeds == "false");
        } else {
            display_richembeds = true;
        }
        $("[name=richembed_toggle_radiobtn][value=" + display_richembeds + "]").prop("checked", true);
        
        var dembed = discord_embed();
        dembed.done(function (data) {
            if (data.instant_invite) {
                $("#modal_invite_btn").show().attr("href", data.instant_invite);
                $("#instant-inv").show().attr("href", data.instant_invite);
            } else {
                $("#modal_invite_btn").hide();
                $("#instant-inv").hide();
            }
        });
        dembed.fail(function () {
            $("#modal_invite_btn").hide();
            $("#instant-inv").hide();
        });
        
        if (getParameterByName("noscroll") != "true") {
            has_handled_noscroll = true;
        }
        
        $(window).resize(function(){
            // For those who decides to hide the embed at first load (display: none), resulting in the messages being not scrolled down.
            if (!has_already_been_initially_resized) {
                has_already_been_initially_resized = true;
                if (has_handled_noscroll) {
                    if (getParameterByName("scrollbartheme")) {
                        $("main").mCustomScrollbar("scrollTo", "bottom", {scrollEasing:"easeOut"});
                    } else {
                        $("main").animate({ scrollTop: $("#chatcontent").height() }, "slow");
                    }
                } else {
                    has_handled_noscroll = true;
                    Materialize.toast('Continue scrolling to read on...', 5000);
                }
            }
        });
        
        $("#chatcontent")
            .mousedown(function () {
                $(window).mousemove(function() {
                    is_dragging_chatcontainer = true;
                    $(window).unbind("mousemove");
                });
            })
            .mouseup(function () {
                var wasDragging = is_dragging_chatcontainer;
                is_dragging_chatcontainer = false;
                $(window).unbind("mousemove");
                if (!wasDragging) {
                    $("#messagebox").focus();
                }
            });
        
        var showScrollbar = getParameterByName("lockscrollbar") == "true";
        if (showScrollbar) {
            showScrollbar = 2;
        } else {
            showScrollbar = 0;
        }
        var scrollbarTheme = getParameterByName("scrollbartheme");
        if (scrollbarTheme) {
            $("main").mCustomScrollbar({
                autoHideScrollbar: !showScrollbar,
                theme: scrollbarTheme,
            });
            $("body").addClass("custom-scrollbars");
        }
        
        if (disabled) {
            Materialize.toast('This server is currently disabled. If you are an administrator of this server, please get in touch with a TitanEmbeds team member to lift the ban.', 100000);
            return;
        }
        
        primeEmbed();
        setInterval(send_socket_heartbeat, 30000);
        if (getParameterByName("username")) {
            $("#custom_username_field").val(getParameterByName("username"));
        }
    });
    
    function changeNotificationSound(sound) {
        var soundTypes = ["newmsgs", "mentions", "nothing"];
        if ($.inArray(sound, soundTypes) != -1) {
            notification_sound_setting = sound;
            $("[name=notification_sound_radiobtn][value=" + sound + "]").prop("checked", true);
            localStorage.setItem("notification_sound", sound);
        }
    }
    
    function changeTheme(theme, keep_custom_css, modifyLocalStore) {
        if (theme === undefined) {
            theme = null;
        }
        if (keep_custom_css === undefined) {
            keep_custom_css = true;
        }
        if (modifyLocalStore === undefined) {
            modifyLocalStore = true;
        }
        if (theme == "") {
          $("#css-theme").attr("href", "");
          $("#user-defined-css").text(user_def_css);
          if (modifyLocalStore) {
              localStorage.removeItem("theme");
          }
        } else if ($.inArray(theme, theme_options) != -1 || theme == null) {
            if (!keep_custom_css) {
                $("#user-defined-css").text("");
            } else {
                $("#user-defined-css").text(user_def_css);
            }
            if (theme) {
                $("#css-theme").attr("href", "/static/themes/" + theme + "/css/style.css");
                if (modifyLocalStore) {
                    localStorage.setItem("theme", theme);
                }
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
            $(".wdt-emoji-picker").hide();
            $("#upload-file-btn").hide();
            $("#send-msg-btn").hide();
        } else {
            $("#visitor_mode_message").hide();
            $("#messagebox").show();
            $("#emoji-tray-toggle").show();
            $(".wdt-emoji-picker").show();
            $("#upload-file-btn").show();
            $("#send-msg-btn").show();
        }
    }

    function primeEmbed() {
        lock_login_fields();

        var guild = query_guild();
        guild.fail(function(data) {
            unlock_login_fields();
            if (data.status == 403 && getParameterByName("create_authenticated_user") == "true" && getParameterByName("sametarget") == "true") {
                wait_for_discord_login();
            } else if (!unauth_captcha_enabled && $("#custom_username_field").length !== 0 && $("#custom_username_field").val().trim() !== "") {
                $("#custom_username_field").trigger(jQuery.Event("keyup", { keyCode: 13 } ));
            } else if (visitors_enabled) {
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
        $("#guestlogin_btn").attr("disabled",true);
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
            socket = null;
        }
        if (guildobj === undefined) {
            var guild = query_guild();
            guild.done(function(data) {
                switch_to_default_channel(data.channels);
                prepare_guild(data);
                $('#loginmodal').modal('close');
                unlock_login_fields();
                setTimeout(displayDblAdvert, 1500);
            });
        } else {
            switch_to_default_channel(guildobj.channels);
            prepare_guild(guildobj);
            $('#loginmodal').modal('close');
            unlock_login_fields();
            setTimeout(displayDblAdvert, 1500);
        }
    }
    
    function displayDblAdvert() {
        var hideDblUntil = "";
        if (localstorage_avaliable) {
            hideDblUntil = localStorage.getItem("hideDiscordBotsOrgVoteAdUntil");
        }
        var now = moment();
        var hideDblUntilMoment = null;
        if (hideDblUntil) {
            hideDblUntilMoment = moment(hideDblUntil);
            if (hideDblUntilMoment.isValid() && hideDblUntilMoment > now) {
                return;
            }
        }
        var dblAdContents = "<i class=\"material-icons right\">close</i></span><span id=\"dblBalloon\"><h6>Loving the Titan, the Discord server widget?</h6><br>Show your appreciation <em>by voting for Titan daily</em> on <a href=\"https://titanembeds.com/vote\" target=\"_blank\">Discord Bot List</a> and get a <span class=\"yellow-text\">golden</span> name and other rewards!";
        $(".brand-logo").showBalloon({
            html: true,
            position: "bottom",
            contents: dblAdContents,
            classname: "dblballoon",
            showComplete: function () {
                $(".dblballoon").css("top", $(".brand-logo").outerHeight() + "px").css("position", "fixed");
                $(".dblballoon").find("i").click(function (event) {
                    event.preventDefault();
                    $(".brand-logo").hideBalloon();
                    localStorage.setItem("hideDiscordBotsOrgVoteAdUntil", now.add(3, "days").toISOString());
                }).css("cursor", "pointer");
            }
        });
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
        global_guest_icon = guildobj.guest_icon;
        emoji_store = guildobj.emojis;
        update_emoji_picker();
        guild_roles_list = guildobj.roles;
        fill_channels(guildobj.channels);
        run_fetch_routine();
        initiate_websockets();
    }

    function fill_channels(channels) {
        guild_channels_list = channels;
        var template = $('#mustache_channellistings').html();
        Mustache.parse(template);
        var template_category = $('#mustache_channelcategory').html();
        Mustache.parse(template_category);
        $("#channels-list").empty();
        var curr_default_channel = selected_channel;
        var categories = [{
            "channel": {id: null, name: "Uncategorized"},
            "children": [],
            "read": true,
        }];
        for (var i = 0; i < channels.length; i++) {
            var chan = channels[i];
            guild_channels[chan.channel.id] = chan;
            if (chan.channel.type == "category") {
                chan.children = [];
                categories.push(chan);
            }
        }
        categories.sort(function(a, b) {
          return parseInt(a.channel.position) - parseInt(b.channel.position);
        });
        for (var i = 0; i < channels.length; i++) {
            var chan = channels[i];
            if (chan.channel.type == "text") {
                var cate = chan.channel.parent_id;
                for (var j = 0; j < categories.length; j++) {
                    var thiscategory = categories[j];
                    if (thiscategory.channel.id == cate) {
                        thiscategory.children.push(chan);
                        break;
                    }
                }
            }
        }
        for (var i = 0; i < categories.length; i++) {
            var cate = categories[i];
            cate.read = false;
            for (var j = 0; j < cate.children.length; j++) {
                var chan = cate.children[j];
                if (chan.channel.type == "text" && chan.read) {
                    cate.read = true;
                    break;
                }
            }
        }
        for (var i = 0; i < categories.length; i++) {
            var cate = categories[i];
            var children = cate.children;
            children.sort(function(a, b) {
              return parseInt(a.channel.position) - parseInt(b.channel.position);
            });
            if (i != 0) {
                if (cate.read) {
                    var rendered_category = Mustache.render(template_category, {"name": cate.channel.name});
                    $("#channels-list").append(rendered_category);
                }
            }
            for (var j = 0; j < children.length; j++) {
                var chan = children[j];
                if (chan.read) {
                    var rendered_channel = Mustache.render(template, {"channelid": chan.channel.id, "channelname": chan.channel.name});
                    $("#channels-list").append(rendered_channel);
                    $("#channel-" + chan.channel.id.toString()).click({"channel_id": chan.channel.id.toString()}, function(event) {
                        select_channel(event.data.channel_id);
                    });
                    if (!selected_channel && (!curr_default_channel || chan.channel.position < curr_default_channel.channel.position)) {
                        curr_default_channel = chan;
                    }
                }
            }
        }
        if (typeof curr_default_channel == "object") {
            if (curr_default_channel == null) {
                $("#messagebox").prop('disabled', true);
                $("#messagebox").prop('placeholder', "NO TEXT CHANNELS");
                $("#upload-file-btn").hide();
                $("#send-msg-btn").hide();
                Materialize.toast("You find yourself in a strange place. You don't have access to any text channels, or there are none in this server.", 20000);
                return;
            }
            selected_channel = curr_default_channel.channel.id;
        }
        var this_channel = guild_channels[selected_channel];
        if (this_channel.write) {
            $("#messagebox").prop('disabled', false);
            $("#messagebox").prop('placeholder', "Enter message");
            $("#upload-file-btn").show();
            $("#send-msg-btn").show();
            $(".wdt-emoji-picker").show();
        } else {
            $("#messagebox").prop('disabled', true);
            $("#messagebox").prop('placeholder', "Messaging is disabled in this channel.");
            $("#upload-file-btn").hide();
            $("#send-msg-btn").hide();
            $(".wdt-emoji-picker").hide();
        }
        if (this_channel.attach_files) {
            $("#upload-file-btn").show();
        } else {
            $("#upload-file-btn").hide();
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
    
    function update_emoji_picker() {
        var emojis = wdtEmojiBundle.listCustomEmojis();
        var short_names = [];
        for (var i = 0; i < emojis.length; i++) {
            short_names.push(emojis.short_name);
        }
        for (var i = 0; i < short_names.length; i++) {
            wdtEmojiBundle.removeCustomEmoji(short_names[i]);
        }
        for (var i = 0; i < emoji_store.length; i++) {
            var emote = emoji_store[i];
            var img_url = "https://cdn.discordapp.com/emojis/" + emote.id;
            if (emote.animated) {
                img_url += ".gif";
            } else {
                img_url += ".png";
            }
            wdtEmojiBundle.addCustomEmoji(emote.name, emote.name, img_url);
        }
    }

    function fill_discord_members(discordmembers) {
        if (!discord_users_list_enabled) {
            if (discordmembers.length == 0 || discordmembers[0].id != 0) {
                return;
            }
        }
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
              openUserCard(event.data.member_id);
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
              openUserCard(event.data.member_id);
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
            var rendered = Mustache.render(template, {"username": member.username, "discriminator": zeroPad(member.discriminator)});
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
                } else if (data.status == 422) {
                    if (data.responseJSON.code == 403) {
                        Materialize.toast("Attempting to add you into the server store has failed. The bot does not have permissions to create instant invite. Therefore, Discord Login has been disabled.", 10000);
                    } else {
                        Materialize.toast("Attempting to add you into the server has failed. Either you are banned, reached 100 servers in Discord, or something else bad has happened.", 10000);
                    }
                } else if (index < 10) {
                    _wait_for_discord_login(index + 1);
                }
            });
        }, 5000);
    }
    
    function openUserCard(user_id) {
        var usr = api_user(user_id);
        usr.done(function (data) {
            for (var i = 0; i < badges_options.length; i++) {
                var badge = badges_options[i];
                if (data.badges.indexOf(badge) != -1) {
                    $("#usercard .badges ." + badge).show();
                } else {
                    $("#usercard .badges ." + badge).hide();
                }
            }
            $("#usercard .avatar").attr("src", data.avatar_url + "?size=512");
            $("#usercard .identity .username").text(data.username);
            $("#usercard .identity .discriminator").text(zeroPad(data.discriminator));
            $("#usercard .identity .discriminator").text(zeroPad(data.discriminator));
            
            var template = $('#mustache_rolebubble').html();
            Mustache.parse(template);
            data.roles.sort(function(a, b) {
                return parseFloat(b.position) - parseFloat(a.position);
            });
            $("#usercard .role .roles").empty();
            var rolecount = 0;
            for (var j = 0; j < data.roles.length; j++) {
                var role = data.roles[j];
                if (role.id == guild_id) {
                    continue;
                }
                rolecount++;
                var color = null;
                if (role.color) {
                    color = "#" + role.color.toString(16);
                }
                var rol = Mustache.render(template, {name: role.name, color: color});
                $("#usercard .role .roles").append(rol);
            }
            if (rolecount) {
                $("#usercard .role").show();
            } else {
                $("#usercard .role").hide();
            }
            
            $("#usercard-mention-btn").off("click");
            $("#usercard-mention-btn").click(function () {
                mention_member(data.id);
                $("#usercard").modal('close');
            });
        });
        
        $("#usercard .offline-text").show();
        $("#usercard .game").hide();
        $("#usercard .bottag").hide();
        for (var i = 0; i < discord_users_list.length; i++) {
            var usr = discord_users_list[i];
            if (usr.id == user_id) {
                $("#usercard .offline-text").hide();
                if (usr.bot) {
                    $("#usercard .bottag").show();
                }
                if (usr.game) {
                    $("#usercard .game").show();
                    $("#usercard .game .text").text(usr.game.name);
                }
                break;
            }
        }
        $("#usercard").modal('open');
    }
    
    function flashElement(element) {
        var opacity = element.css("opacity");
        for (var i = 0; i < 3; i++) {
            element.animate({opacity: 0}, "fast");
            element.animate({opacity: 100}, "fast");
        }
        element.css("opacity", opacity);
    }

    function select_channel(channel_id, animate_it, acknowledge_nsfw) {
        if (selected_channel != channel_id && guild_channels[channel_id] && guild_channels[channel_id].read) {
            if (guild_channels[channel_id].channel.nsfw && !acknowledge_nsfw) {
                $("#proceed_nsfw_btn").attr("channel_id", channel_id);
                $("#proceed_nsfw_btn").attr("should_animate", animate_it ? 1 : 0);
                $("#nsfwmodal").modal("open");
                return;
            }
            if (animate_it) {
                if ($("#guild-btn").is(":visible")) {
                    $("#guild-btn").sideNav("show");
                }
                $("#channel-"+channel_id)[0].scrollIntoView({behavior: "smooth"});
                flashElement($("#channel-"+channel_id));
                var timeout = 400;
                if ($("#guild-btn").is(":visible")) {
                    timeout = 1000;
                }
                setTimeout(function () {
                    if ($("#guild-btn").is(":visible")) {
                        $("#guild-btn").sideNav("hide");
                    }
                    select_channel(channel_id, false, true);
                }, timeout);
                return;
            }
            selected_channel = channel_id;
            last_message_id = null;
            $("#channels-list > li.active").removeClass("active");
            $("#channel-"+selected_channel).parent().addClass("active");
            run_fetch_routine();
        }
    }

    function replace_message_mentions(message) {
        var mentions = message.mentions;
        var template = $('#mustache_discordmention').html();
        Mustache.parse(template);
        for (var i = 0; i < mentions.length; i++) {
            var mention = mentions[i];
            var username = mention.username;
            if (mention.nickname) {
                username = mention.nickname;
            }
            var rendered = Mustache.render(template, {"username": username, "discriminator": zeroPad(mention.discriminator)}).trim();
            message.content = message.content.replace(new RegExp("&lt;@" + mention.id + "&gt;", 'g'), rendered);
            message.content = message.content.replace(new RegExp("&lt;@!" + mention.id + "&gt;", 'g'), rendered);
        }
        
        var template = $("#mustache_rolemention").html();
        Mustache.parse(template);
        for (var i = 0; i < guild_roles_list.length; i++) {
            var role = guild_roles_list[i];
            var roleobj = {"rolename": role.name};
            if (role.color) {
                roleobj.color = "#" + role.color.toString(16);
            }
            var rendered = Mustache.render(template, roleobj).trim();
            message.content = message.content.replace("&lt;@&amp;" + role.id + "&gt;", rendered);
        }
        return message;
    }

    function getPosition(string, subString, index) {
       return string.split(subString, index).join(subString).length;
    }

    function format_bot_message(message) {
        if (message.author.id == bot_client_id && (message.content.includes("**") && ( (message.content.includes("<")&&message.content.includes(">")&&!message.content.startsWith("<@")) || (message.content.includes("[") && message.content.includes("]")) ))) {
            var usernamefield = message.content.substring(getPosition(message.content, "**", 1)+3, getPosition(message.content, "**", 2)-1);
            if (message.content.startsWith("(Titan Dev) ")) {
                message.content = message.content.substring(usernamefield.length + 18);
            } else {
                message.content = message.content.substring(usernamefield.length + 7);
            }
            message.author.username = usernamefield.split("#")[0];
            message.author.nickname = null;
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
            if (message.attachments[i].url.endsWith(".png") || message.attachments[i].url.endsWith(".jpg") || message.attachments[i].url.endsWith(".jpeg") || message.attachments[i].url.endsWith(".gif")) {
                attach += "<img class=\"attachment materialboxed\" src=\"" + message.attachments[i].url + "\">";
            } else if (message.attachments[i].url.endsWith(".mp4")) {
                attach += "<video class=\"player\" src=\"" + message.attachments[i].url + "\" frameborder=\"0\" allow=\"encrypted-media\" allowfullscreen controls preload poster=\"" + message.attachments[i].proxy_url + "?format=png\"></video>";
            } else {
                attach += message.attachments[i].url;
            }
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
    
    function play_notification_sound(type) { // type can be mention or new
        if (notification_sound_setting == "nothing") {
            return;
        } else if (notification_sound_setting == "mentions" && type != "mention") {
            return;
        }
        if (notification_sound.playState == 0) {
            notification_sound.play();
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
            var pattern = "&lt;#" + channelids[i] + "&gt;";
            var elem = "<span class=\"channellink\" channelid=\"" + channelids[i] + "\">#" + guild_channels[channelids[i]].channel.name + "</span>";
            message.content = message.content.replace(new RegExp(pattern, "g"), elem);
        }
        return message;
    }
    
    function parse_emoji_in_message(message) {
        var template = $('#mustache_message_emoji').html();
        Mustache.parse(template);
        for (var i = 0; i < emoji_store.length; i++) {
            var emoji = emoji_store[i];
            var emoji_format = "";
            if (emoji.animated) {
                emoji_format = "&lt;a:" + emoji.name + ":" + emoji.id + "&gt;";
            } else {
                emoji_format = "&lt;:" + emoji.name + ":" + emoji.id + "&gt;";
            }
            var rendered = Mustache.render(template, {"id": emoji.id, "name": emoji.name, "animated": emoji.animated}).trim();
            message.content = message.content.replaceAll(emoji_format, rendered);
        }
        var rendered = Mustache.render(template, {"id": "$2", "name": "$1"}).trim();
        message.content = message.content.replace(/&lt;:(.*?):(.*?)&gt;/g, rendered);
        rendered = Mustache.render(template, {"id": "$2", "name": "$1", "animated": true}).trim();
        message.content = message.content.replace(/&lt;a:(.*?):(.*?)&gt;/g, rendered);
        message.content = twemoji.parse(message.content, {
            className: "message_emoji",
            callback: function(icon, options, variant) { // exclude special characters
                switch (icon) {
                    case 'a9':      // © copyright
                    case 'ae':      // ® registered trademark
                    case '2122':    // ™ trademark
                        return false;
                }
                return ''.concat(options.base, options.size, '/', icon, options.ext);
            }
        });
        return message;
    }
    
    function parse_message_markdown(text) {
        var geturl_regex = /(\(.*?)?\b((?:https?|ftp|file):\/\/[-a-z0-9+&@#\/%?=~_()|!:,.;]*[-a-z0-9+&@#\/%=~_()|])/ig;
        var links = text.match(geturl_regex); // temporarily remove urls so markdown won't mark inside of the url
        if (links) {
            for (var i = 0; i < links.length; i++) {
                text = text.replace(links[i], "$LINK"+i+"$");
            }
        }
        text = text.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");
        text = text.replace(/\*(.*?)\*/g, "<i>$1</i>");
        text = text.replace(/__(.*?)__/g, "<u>$1</u>");
        text = text.replace(/_(.*?)_/g, "<i>$1</i>");
        text = text.replace(/~~(.*?)~~/g, "<del>$1</del>");
        text = text.replace(/\`\`\`([^]+?)\`\`\`/g, "<code class=\"blockcode\">$1</code>");
        text = text.replace(/\`(.*?)\`/g, "<code>$1</code>");
        if (links) {
            for (var i = 0; i < links.length; i++) {
                text = text.replace("$LINK"+i+"$", links[i]);
            }
        }
        return text;
    }
    
    function render_code_highlighting(element) {
        for (var i = 0; i < element.length; i++) {
            var elem = $(element[i]);
            var codetext = elem.text();
            var splitted = codetext.split("\n");
            if (splitted.length > 1) {
                var firstLine = splitted[0];
                if (!(/^\s/.test(firstLine))) { // make sure no whitespace at begining
                    var firstLineSplitted = firstLine.split(/[ ]+/); // split at whitespace
                    if (firstLineSplitted.length == 1 && firstLineSplitted[0] != "") { // only one token and the token is not empty
                        var language = firstLineSplitted[0]; // assume token is lang
                        if (hljs.getLanguage(language)) {
                            splitted.splice(0, 1); // delete first line
                            var restOfCode = splitted.join("\n");
                            var highlighted = hljs.highlight(language, restOfCode, true);
                            elem.html(highlighted.value);
                        }
                    }
                }
            }
        }
    }
    
    function generate_avatar_url(user_id, avatar_hash, message_contents) {
        if (message_contents === undefined) {
            message_contents = null;
        }
        if (user_id == bot_client_id && (message_contents.includes("**") && ( (message_contents.includes("<")&&message_contents.includes(">")) || (message_contents.includes("[") && message_contents.includes("]")) ))) {
            return global_guest_icon;
        } else {
            return "https://cdn.discordapp.com/avatars/" + user_id + "/" + avatar_hash + ".png";
        }
    }
    
    function parse_message_embeds(embeds) {
        var emb = [];
        if (display_richembeds) {
            for (var i = 0; i < embeds.length; i++) {
                var disembed = embeds[i];
                // if ($.inArray(disembed.type, ["rich", "link", "video"]) == -1) {
                //     continue;
                // }
                
                if (disembed.type == "image") {
                    var img = "<img class=\"image attachment materialboxed\" src=\"" + disembed.thumbnail.proxy_url + "\">";
                    emb.push(img);
                    continue;
                }
                
                disembed.isVideo = false;
                if (disembed.type == "video") {
                    disembed.isVideo = true;
                    if (disembed.video) {
                        var url = new URL(disembed.video.url);
                        if (url.hostname.endsWith("twitch.tv")) {
                            if (url.searchParams.has("autoplay")) {
                                url.searchParams.set("autoplay", "false");
                                disembed.video.url = url.toString();
                            }
                        }
                    }
                }
                disembed.toRenderFooter = false;
                if (disembed.footer) {
                    disembed.toRenderFooter = true;
                } else if (disembed.timestamp) {
                    disembed.toRenderFooter = true;
                }
                disembed.footerVerticalBar = disembed.footer && disembed.timestamp;
                if (disembed.timestamp) {
                    disembed.formatted_timestamp = moment(disembed.timestamp).format('ddd MMM Do, YYYY [at] h:mm A');
                }
                if (disembed.color) {
                    disembed.hexColor = "#" + disembed.color.toString(16);
                }
                var template = $('#mustache_richembed').html();
                Mustache.parse(template);
                var rendered = Mustache.render(template, disembed);
                emb.push(rendered);
            }
        }
        return emb;
    }
    
    function parse_message_reactions(reactions) {
        var reacts = []
        var template = $("#mustache_reactionchip").html();
        Mustache.parse(template);
        for (var i = 0; i < reactions.length; i++) {
            var disreact = reactions[i];
            var emoji = disreact.emoji;
            if (emoji.id) {
                disreact.img_url = "https://cdn.discordapp.com/emojis/" + emoji.id;
                if (emoji.animated) {
                    disreact.img_url += ".gif";
                } else {
                    disreact.img_url += ".png";
                }
            } else {
                disreact.img_url = $(twemoji.parse(emoji.name)).attr("src");
            }
            var rendered = Mustache.render(template, disreact);
            reacts.push(rendered);
        }
        return reacts;
    }
    
    function scroll_on_dom_update() {
        var scrollRegion = $(window).height() / 2;
        if (!getParameterByName("scrollbartheme") && $("main").prop("scrollHeight") - ($("main").scrollTop() + $("main").outerHeight()) < scrollRegion) {
            $("main").scrollTop($("#chatcontent").outerHeight());
        }
    }
    
    function format_new_member_message(message) {
        var formats = [
            "{0} just joined the server - glhf!",
            "{0} just joined. Everyone, look busy!",
            "{0} just joined. Can I get a heal?",
            "{0} joined your party.",
            "{0} joined. You must construct additional pylons.",
            "Ermagherd. {0} is here.",
            "Welcome, {0}. Stay awhile and listen.",
            "Welcome, {0}. We were expecting you ( ͡° ͜ʖ ͡°)",
            "Welcome, {0}. We hope you brought pizza.",
            "Welcome {0}. Leave your weapons by the door.",
            "A wild {0} appeared.",
            "Swoooosh. {0} just landed.",
            "Brace yourselves. {0} just joined the server.",
            "{0} just joined. Hide your bananas.",
            "{0} just arrived. Seems OP - please nerf.",
            "{0} just slid into the server.",
            "A {0} has spawned in the server.",
            "Big {0} showed up!",
            "Where’s {0}? In the server!",
            "{0} hopped into the server. Kangaroo!!",
            "{0} just showed up. Hold my beer.",
            "Challenger approaching - {0} has appeared!",
            "It's a bird! It's a plane! Nevermind, it's just {0}.",
            "It's {0}! Praise the sun! [T]/",
            "Never gonna give {0} up. Never gonna let {0} down.",
            "Ha! {0} has joined! You activated my trap card!",
            "Cheers, love! {0}'s here!",
            "Hey! Listen! {0} has joined!",
            "We've been expecting you {0}",
            "It's dangerous to go alone, take {0}!",
            "{0} has joined the server! It's super effective!",
            "Cheers, love! {0} is here!",
            "{0} is here, as the prophecy foretold.",
            "{0} has arrived. Party's over.",
            "Ready player {0}",
            "{0} is here to kick butt and chew bubblegum. And {0} is all out of gum.",
            "Hello. Is it {0} you're looking for?",
            "{0} has joined. Stay a while and listen!",
            "Roses are red, violets are blue, {0} joined this server with you",
        ];
        var index = moment(message.timestamp).unix() % formats.length;
        var formatted = formats[index].replace(/\{0\}/g, message.author.username);
        return "<i class=\"material-icons new-member-arrow\">arrow_forward</i> " + formatted;
    }

    function fill_discord_messages(messages, jumpscroll, replace) {
        if (replace === undefined) {
            replace = null;
        }
        if (messages.length == 0) {
            return last_message_id;
        }
        var last = 0;
        var template = $('#mustache_usermessage').html();
        Mustache.parse(template);
        for (var i = messages.length-1; i >= 0; i--) {
            var message = messages[i];
            if (message.author.avatar) {
                var avatar = generate_avatar_url(message.author.id, message.author.avatar, message.content);
            } else {
                var avatar = global_guest_icon;
            }
            message = format_bot_message(message);
            message = parse_message_time(message);
            message.content = message.content.replaceAll("\\<", "<");
            message.content = message.content.replaceAll("\\>", ">");
            message.content = escapeHtml(message.content);
            message = replace_message_mentions(message);
            message = parse_message_attachments(message);
            message.content = parse_message_markdown(message.content);
            message = parse_channels_in_message(message);
            message = parse_emoji_in_message(message);
            message.content = message.content.replace(/&lt;https:\/\/(.*?)&gt;/g, "https://$1");
            message.content = message.content.replace(/&lt;http:\/\/(.*?)&gt;/g, "http://$1");
            if (message.type == 7) {
                message.content = format_new_member_message(message);
            }
            var username = message.author.username;
            if (message.author.nickname) {
                username = message.author.nickname;
            }
            var rendered = Mustache.render(template, {"id": message.id, "full_timestamp": message.formatted_timestamp, "time": message.formatted_time, "username": username, "discriminator": zeroPad(message.author.discriminator), "avatar": avatar, "content": nl2br(message.content)});
            if (replace == null) {
                $("#chatcontent").append(rendered);
                handle_last_message_mention();
                $("#chatcontent p:last-child").attr("timestamp", message.timestamp);
                $("#chatcontent p:last-child").find(".blockcode").find("br").remove(); // Remove excessive breaks in codeblocks
                render_code_highlighting($("#chatcontent p:last-child").find(".blockcode"));
                $("#chatcontent .chatusername").last().click(function () {
                    var discordid = $(this).parent().attr("discord_userid");
                    if (discordid) {
                        openUserCard(discordid);
                    }
                });
                $("#chatcontent p:last-child").find(".channellink").click(function () {
                    select_channel($(this).attr("channelid"), true);
                });
                if (message.type == 7) {
                    $("#chatcontent p:last-child").addClass("new-member");
                }
            } else {
                replace.html($(rendered).html());
                replace.find(".blockcode").find("br").remove();
                render_code_highlighting(replace.find(".blockcode"));
                replace.find(".channellink").click(function () {
                    select_channel($(this).attr("channelid"), true);
                });
            }
            var embeds = parse_message_embeds(message.embeds);
            $("#discordmessage_"+message.id).parent().find("span.embeds").text("");
            for(var j = 0; j < embeds.length; j++) {
                $("#discordmessage_"+message.id).parent().find("span.embeds").append(embeds[j]);
            }
            var reactions = parse_message_reactions(message.reactions);
            $("#discordmessage_"+message.id).parent().find("span.reactions").text("");
            for(var j = 0; j < reactions.length; j++) {
                $("#discordmessage_"+message.id).parent().find("span.reactions").append(reactions[j]);
            }
            var usrcachekey = username + "#" + message.author.discriminator;
            if (usrcachekey.startsWith("(Titan Dev) ")) {
                usrcachekey = usrcachekey.substr(12);
            }
            if (!(usrcachekey in message_users_cache)) {
                message_users_cache[usrcachekey] = {"data": {}, "msgs": []};
            }
            message_users_cache[usrcachekey]["msgs"].push(message.id);
            last = message.id;
        }
        if (replace == null) {
            play_notification_sound("new");
        }
        if ($("#chatcontent p:last-child.mentioned").length) {
            play_notification_sound("mention");
        }
        
        if (replace == null && jumpscroll) {
            if (!has_handled_noscroll) {
                has_handled_noscroll = true;
                Materialize.toast('Continue scrolling to read on...', 5000);
            } else {
                if (getParameterByName("scrollbartheme")) {
                    if ($(window).height() < $("main .mCSB_container").height()) {
                        setIntervalX(function () {
                            $("main .mCSB_container").animate({
                                top: -1 * ($("main .mCSB_container").height() - $(window).height())
                            }, "slow", function () {
                                $("main").mCustomScrollbar("update");
                            });
                        }, 1000, 3);
                    }
                } else {
                    setIntervalX(function () {
                        $("main").animate({ scrollTop: $("#chatcontent").height() }, "slow");
                    }, 1000, 3);
                }
            }
        }
        $("#chatcontent img").on("load", scroll_on_dom_update);
        $('#chatcontent').linkify({
            target: "_blank"
        });
        $('.tooltipped').tooltip();
        $('.materialboxed').materialbox();
        process_message_users_cache();
        return last;
    }

    function run_fetch_routine() {
        var channel_id = selected_channel;
        var fet;
        var jumpscroll;
        if (channel_id == null) {
            return;
        }
        $("#message-spinner").fadeIn();
        if (last_message_id == null) {
            $("#chatcontent").empty();
            fet = fetch(channel_id);
            jumpscroll = true;
        } else {
            fet = fetch(channel_id, last_message_id);
            jumpscroll = false;
            if (last_message_id) {
                jumpscroll = element_in_view($('#discordmessage_'+last_message_id).parent());
            }
        }
        fet.done(function(data) {
            socket_error_should_refetch = false;
            var status = data.status;
            if (visitor_mode) {
                update_embed_userchip(false, null, "Titan", null, "0001", null);
                update_change_username_modal();
            } else {
                update_embed_userchip(status.authenticated, status.avatar, status.username, status.nickname, status.user_id, status.discriminator);
                update_change_username_modal(status.authenticated, status.username);
                current_user_discord_id = status.user_id;
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
            });
            $("#message-spinner").removeClass("error");
            $("#message-spinner").fadeOut();
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
            $("#message-spinner").addClass("error");
        });
    }
    
    function process_message_users_cache() {
        var keys = Object.keys(message_users_cache);
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            var hashpos = key.lastIndexOf("#");
            var name = key.substring(0, hashpos);
            var discriminator = key.substring(hashpos+1);
            if (name.startsWith("(Titan Dev) ")) {
                name = name.substring(12);
            }
            var key_helper = name + "#" + discriminator;
            if (jQuery.isEmptyObject(message_users_cache[key_helper]["data"])) {
                if (socket && socket_identified) {
                    socket.emit("lookup_user_info", {"guild_id": guild_id, "name": name, "discriminator": discriminator});
                }
            } else {
                process_message_users_cache_helper(key_helper, message_users_cache[key_helper]["data"]);
            }

        }
    }
    
    function process_message_users_cache_helper(key, usr) {
        var msgs = message_users_cache[key]["msgs"];
        while (msgs.length > 0) {
            var element = $("#discordmessage_"+msgs.pop());
            var parent = element.parent();
            if (usr.color) {
                parent.find(".chatusername").css("color", "#"+usr.color);
            } else {
                parent.find(".chatusername").css("color", null);
            }
            if (usr.discordbotsorgvoted) {
                parent.find(".chatusername").addClass("discordbotsorgvoted");
            }
            if (usr.avatar_url) {
                parent.find(".authoravatar").prop("src", usr.avatar_url);
            }
            if (usr.roles) {
                parent.attr("discord_userroles", usr.roles.join(" "));
            }
            parent.attr("discord_userid", usr.id);
        }
        collapse_messages();
    }
    
    function collapse_messages() {
        var allMessages = $('[id^="discordmessage_"]').parent();
        for (var i = 1; i < allMessages.length; i++) {
            var last = $(allMessages[i - 1]);
            var current = $(allMessages[i]);
            if (!last.hasClass("new-member") && last.attr("discord_userid") == current.attr("discord_userid") && current.attr("discord_userid") && moment(current.attr("timestamp")).isSame(moment(last.attr("timestamp")), "hour")) {
                current.addClass("collapsed");
            } else {
                current.removeClass("collapsed");
            }
        }
    }

    function update_embed_userchip(authenticated, avatar, username, nickname, userid, discrim) {
        if (discrim === undefined) {
            discrim = null;
        }
        if (authenticated) {
            $("#currentuserimage").attr("src", avatar);
            $("#curuser_name").text(username);
            $("#curuser_discrim").text("#" + discrim);
            current_username_discrim = "#" + discrim;
        } else {
            $("#currentuserimage").attr("src", global_guest_icon);
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
    
    function update_change_username_modal(authenticated, username) {
        if (authenticated === undefined) {
            authenticated = null;
        }
        if (username === undefined) {
            username = null;
        }
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
            do_guest_login();
        }
    });
    
    $("#guestlogin_btn").click(function () {
        do_guest_login();
    });

    function do_guest_login() {
        if (!(new RegExp(/^[a-z\d\-_\s]+$/i).test($("#custom_username_field").val()))) {
            Materialize.toast('Illegal username provided! Only alphanumeric, spaces, dashes, and underscores allowed in usernames.', 10000);
            return;
        }
        if($("#custom_username_field").val().length >= 2 && $("#custom_username_field").val().length <= 32) {
            $("#custom_username_field").blur();
            if (unauth_captcha_enabled) {
                $('#recaptchamodal').modal('open');
            } else {
                submit_unauthenticated_captcha();
            }
        }
    }

    $("#submit-unauthenticated-captcha-btn").click(function(){
        lock_login_fields();
        var usr = create_unauthenticated_user($("#custom_username_field").val(), grecaptcha.getResponse());
        usr.done(function(data) {
            grecaptcha.reset();
            setVisitorMode(false);
            initialize_embed();
        });
        usr.fail(function(data) {
            if (data.status == 429) {
                Materialize.toast('Sorry! You are allowed to log in as a guest three times in a span of 30 minutes.', 10000);
            } else if (data.status == 403) {
                Materialize.toast('Authentication error! You have been banned.', 10000);
            } else if (data.status == 406) {
                Materialize.toast('Illegal username provided! Only alphanumeric, spaces, dashes, and underscores allowed in usernames.', 10000);
            } else if (data.status == 412) {
                Materialize.toast("reCAPTCHA reponse has failed. Try again?", 10000);
            }
            unlock_login_fields();
            setVisitorMode(true);
        });
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
                    if (socket) {
                        run_fetch_routine();
                        socket.disconnect();
                        socket = null;
                    }
                    initiate_websockets();
                });
                usr.fail(function(data) {
                    if (data.status == 429) {
                        Materialize.toast('Sorry! You are allowed to change your username once every 10 minutes.', 10000);
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
    
    function stringToDefaultEmote(input) {
        var map = {
            "<3": "\u2764\uFE0F",
            "</3": "\uD83D\uDC94",
            ":D": "\uD83D\uDE00",
            ":)": "\uD83D\uDE03",
            ";)": "\uD83D\uDE09",
            ":(": "\uD83D\uDE12",
            ":p": "\uD83D\uDE1B",
            ";p": "\uD83D\uDE1C",
            ":'(": "\uD83D\uDE22"
        };
        for (var i in map) {
            var escaped = i.replace(/([()[{*+.$^\\|?])/g, '\\$1');
            escaped = "(\\s|^)(" + escaped + ")(\\s|$)";
            var regex = new RegExp(escaped, 'gim');
            input = input.replace(regex, "$1" + map[i] + "$3");
        }
        return input;
    }
    
    $("#chatcontent").bind("click", function () {
        $("#mention-picker").hide();
        wdtEmojiBundle.close();
    });
    
    $("#messagebox").bind("click", function () {
        wdtEmojiBundle.close();
    });
    
    $('#messagebox').bind('input keydown click', function(event) {
        if (event.type == "keydown" && (event.which == 38 || event.which == 40 || event.which == 13) && $("#mention-picker").is(":visible")) {
            return;
        }
        var cursorAt = $(this).caret();
        var input = $(this).val().substr(0, cursorAt);
        var lastWord = input.match(/@\w+$/);
        if (lastWord == null) {
            $("#mention-picker").hide();
            return;
        }
        lastWord = lastWord[0];
        if (lastWord.charAt(0) != "@") {
            $("#mention-picker").hide();
            return;
        }
        lastWord = lastWord.substr(1);
        if (all_users.length == 0) {
            var usrs = list_users();
            usrs.done(function (lst) {
                all_users = lst;
            });
        }
        var template = $('#mustache_usermentionchoices').html();
        Mustache.parse(template);
        var users = [];
        for (var i = 0; i < all_users.length; i++) {
            var usr = all_users[i];
            if (usr.username.toLowerCase().indexOf(lastWord.toLowerCase()) > -1 || (usr.nickname && usr.nickname.toLowerCase().indexOf(lastWord.toLowerCase()) > -1)) {
                var displayname = usr.username;
                if (usr.nickname) {
                    displayname = usr.nickname;
                }
                users.push({
                    id: usr.id,
                    avatar: usr.avatar_url,
                    username: usr.username,
                    discriminator: usr.discriminator,
                    displayname: displayname
                });
            }
        }
        if (users.length == 0) {
            $("#mention-picker").hide();
            return;
        }
        $("#mention-picker").show();
        $("#mention-picker-content").html("");
        for (var i = 0; i < users.length; i++) {
            var usr = users[i];
            var rendered = $(Mustache.render(template, usr));
            rendered.hover(function () {
                $("#mention-picker .mention-choice.selected").removeClass("selected");
                $(this).addClass("selected");
            });
            rendered.click(function () {
                var usrid = $(this).attr("discorduserid");
                var val = $("#messagebox").val().replace("@" + lastWord, "[@" + usrid + "] ");
                $("#messagebox").val(val);
                $("#mention-picker").hide();
                $("#messagebox").focus();
            });
            $("#mention-picker-content").append(rendered);
        }
        $("#mention-picker .mention-choice.selected").removeClass("selected");
        $("#mention-picker .mention-choice").first().addClass("selected");
    });
    
    $("#messagebox").keyup(function (event) {
        if (event.keyCode == 16) {
            shift_pressed = false;
        }
    });

    $("#messagebox").keydown(function(event){
        if ($("#mention-picker").is(":visible")) {
            if ((event.which == 38 || event.which == 40)) {
                event.preventDefault();
                var choices = $("#mention-picker .mention-choice");
                var selected = $("#mention-picker .mention-choice.selected");
                var index = choices.index(selected);
                selected.removeClass("selected");
                if (event.which == 40) {
                    if (index == choices.length - 1) {
                        $(choices.get(0)).addClass("selected");
                    } else {
                        $(choices.get(index + 1)).addClass("selected");
                    }
                } else {
                    if (index == 0) {
                        $(choices.get(choices.length - 1)).addClass("selected");
                    } else {
                        $(choices.get(index - 1)).addClass("selected");
                    }
                }
                $("#mention-picker .mention-choice.selected")[0].scrollIntoView({behavior: "instant", block: "center", inline: "center"});
                return;
            }
            if (event.which == 13) {
                event.preventDefault();
                $("#mention-picker .mention-choice.selected").click();
                return;
            }
            if (event.which == 27) {
                $("#mention-picker").hide();
            }
        }
        
        
        if ($(this).val().length == 1) {
            $(this).val($.trim($(this).val()));
        }
        if (event.keyCode == 16) {
            shift_pressed = true;
        }
        if(event.keyCode == 13 && !shift_pressed && ($(this).val().length >= 1 || $("#fileinput").val().length >= 1)) {
            $(this).val($.trim($(this).val()));
            $(this).blur();
            $("#messagebox-filemodal").attr('readonly', true);
            $("#proceed_fileupload_btn").attr("disabled", true);
            $("#messagebox").attr('readonly', true);
            $("#send-msg-btn").attr("disabled", true);
            var emojiConvertor = new EmojiConvertor();
            emojiConvertor.init_env();
            emojiConvertor.replace_mode = "unified";
            emojiConvertor.allow_native = true;
            var messageInput = emojiConvertor.replace_colons($(this).val());
            messageInput = stringToDefaultEmote(messageInput);
            var file = null;
            if ($("#fileinput")[0].files.length > 0) {
                file = $("#fileinput")[0].files[0];
            }
            $("#filemodalprogress").show();
            var funct = post(selected_channel, messageInput, file);
            funct.done(function(data) {
                $("#messagebox").val("");
                $("#messagebox-filemodal").val("");
                $("#fileinput").val("");
                $("#filemodal").modal("close");
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
                    Materialize.toast('You are sending messages too fast! 1 message per ' + post_timeout + ' seconds', 10000);
                } else if (data.status == 413) {
                    Materialize.toast('Your file is too powerful! The maximum file size is 4 megabytes.', 5000);
                }
            });
            funct.always(function() {
                $("#messagebox").attr('readonly', false);
                $("#messagebox-filemodal").attr('readonly', false);
                $("#proceed_fileupload_btn").attr("disabled", false);
                $("#filemodalprogress").hide();
                $("#send-msg-btn").attr("disabled", false);
                if ($("#filemodal").is(":visible")) {
                    $("#messagebox-filemodal").focus();
                } else {
                    $("#messagebox").focus();
                }
            });
        }
    });
    
    $("#messagebox-filemodal").keyup(function (event) {
        if (event.keyCode == 16) {
            shift_pressed = false;
        }
    });
    
    $("#messagebox-filemodal").keydown(function (event) {
        if ($(this).val().length == 1) {
            $(this).val($.trim($(this).val()));
        }
        if (event.keyCode == 16) {
            shift_pressed = true;
        }
        
        if(event.keyCode == 13 && !shift_pressed) {
            $(this).val($.trim($(this).val()));
            $(this).blur();
            $("#messagebox").val($(this).val());
            $("#messagebox").trigger(jQuery.Event("keydown", { keyCode: 13 } ));
        }
    });
    
    $("#send-msg-btn").click(function () {
        $("#messagebox").focus();
        $("#messagebox").trigger(jQuery.Event("keydown", { keyCode: 13 } ));
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
        if (socket || !shouldUtilizeGateway) {
            return;
        }
        
        socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + "/gateway", {path: '/gateway', transports: ['websocket']});
        socket.on('connect', function () {
            socket.emit('identify', {"guild_id": guild_id, "visitor_mode": visitor_mode});
        });

        socket.on('hello', function (msg) {
            var gateway_identifier = msg.gateway_identifier;
            if (!gateway_identifier) {
                gateway_identifier = "null";
            }
            console.log("%c[TitanEmbeds]%cConnected to gateway via%c" + gateway_identifier, 'color:aqua;background-color:black;border:1px solid black;padding: 3px;', 'color:white;background-color:black;border:1px solid black;padding: 3px;', 'color:white;background-color:black;border:1px solid black;font-family: Courier;padding: 3px;');
        });

        socket.on("identified", function () {
            socket_identified = true;
            process_message_users_cache();
        })
        
        socket.on("disconnect", function () {
            socket_identified = false;
        });
        
        socket.on("revoke", function () {
            socket.disconnect();
            socket = null;
            $('#loginmodal').modal('open');
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
            var jumpscroll = false;
            if (last_message_id) {
                jumpscroll = element_in_view($('#discordmessage_'+last_message_id).parent());
            }
            last_message_id = fill_discord_messages([msg], jumpscroll);
        });
        
        socket.on("MESSAGE_DELETE", function (msg) {
            var msgchan = msg.channel_id;
            if (selected_channel != msgchan) {
                return;
            }
            $("#discordmessage_"+msg.id).parent().remove();
            var lastelem = $("#chatcontent").find("[id^=discordmessage_]");
            if (lastelem.length) {
                last_message_id = lastelem.last().attr('id').substring(15);
            } else {
                last_message_id = null;
            }
        });
        
        socket.on("MESSAGE_UPDATE", function (msg) {
            var msgelem = $("#discordmessage_"+msg.id);
            if (msgelem.length == 0) {
                return;
            }
            var msgelem_parent = msgelem.parent();
            fill_discord_messages([msg], false, msgelem_parent);
        });
        
        socket.on("MESSAGE_REACTION_ADD", function (msg) {
            var msgelem = $("#discordmessage_"+msg.id);
            if (msgelem.length == 0) {
                return;
            }
            var msgelem_parent = msgelem.parent();
            fill_discord_messages([msg], false, msgelem_parent);
        });
        
        socket.on("MESSAGE_REACTION_REMOVE", function (msg) {
            var msgelem = $("#discordmessage_"+msg.id);
            if (msgelem.length == 0) {
                return;
            }
            var msgelem_parent = msgelem.parent();
            fill_discord_messages([msg], false, msgelem_parent);
        });
        
        socket.on("MESSAGE_REACTION_REMOVE_ALL", function (msg) {
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
            if (all_users.length == 0) {
                return;
            }
            all_users.push({
                "id": usr.id,
                "avatar": usr.avatar,
                "avatar_url": generate_avatar_url(usr.id, usr.avatar),
                "username": usr.username,
                "nickname": usr.nickname,
                "discriminator": usr.discriminator
            });
        });
        
        socket.on("GUILD_MEMBER_UPDATE", function (usr) {
            if (usr.id == current_user_discord_id) {
                update_socket_channels();
                socket.emit("current_user_info", {"guild_id": guild_id});
            }
            var updatedUser = false;
            for (var i = 0; i < all_users.length; i++) {
                if (usr.id == all_users[i].id) {
                    var u = all_users[i];
                    u.avatar = usr.avatar;
                    u.avatar_url = generate_avatar_url(usr.id, usr.avatar);
                    u.username = usr.username;
                    u.nickname = usr.nickname;
                    u.discriminator = usr.discriminator;
                    updatedUser = true;
                    break;
                }
            }
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
            if (!updatedUser) {
                all_users.push({
                    "id": usr.id,
                    "avatar": usr.avatar,
                    "avatar_url": generate_avatar_url(usr.id, usr.avatar),
                    "username": usr.username,
                    "nickname": usr.nickname,
                    "discriminator": usr.discriminator
                });
            }
        });

        socket.on("GUILD_MEMBER_REMOVE", function (usr) {
            for (var i = 0; i < all_users.length; i++) {
                if (usr.id == all_users[i].id) {
                    all_users.splice(i, 1);
                    break;
                }
            }
            for (var i = 0; i < discord_users_list.length; i++) {
                if (usr.id == discord_users_list[i].id) {
                    discord_users_list.splice(i, 1);
                    fill_discord_members(discord_users_list);
                    break;
                }
            }
        });

        socket.on("GUILD_EMOJIS_UPDATE", function (emo) {
            emoji_store = emo;
            update_emoji_picker();
        });
        
        socket.on("GUILD_UPDATE", function (guil) {
            $("#guild_name").text(guil.name);
            if (guil.icon) {
                $("#guild_icon").attr("src", guil.icon_url);
                $("#guild_icon").show();
            } else {
                $("#guild_icon").hide();
            }
        });
        
        socket.on("CHANNEL_DELETE", function (chan) {
            for (var i = 0; i < guild_channels_list.length; i++) {
                var thatchannel = guild_channels_list[i];
                if (thatchannel.channel.id == chan.id) {
                    guild_channels_list.splice(i, 1);
                    fill_channels(guild_channels_list);
                    return;
                }
            }
        });
        
        socket.on("CHANNEL_UPDATE", function (chan) {
            update_socket_channels();
        });
        
        socket.on("CHANNEL_CREATE", function (chan) {
            update_socket_channels();
        });
        
        socket.on("GUILD_ROLE_CREATE", function (role) {
            update_socket_channels();
            guild_roles_list.push(role);
        });
        
        socket.on("GUILD_ROLE_UPDATE", function (role) {
            update_socket_channels();
            for (var i = 0; i < guild_roles_list.length; i++) {
                if (guild_roles_list[i].id == role.id) {
                    guild_roles_list.splice(i, 1);
                    guild_roles_list.push(role);
                    return;
                }
            }
        });
        
        socket.on("GUILD_ROLE_DELETE", function (role) {
            update_socket_channels();
            for (var i = 0; i < guild_roles_list.length; i++) {
                if (guild_roles_list[i].id == role.id) {
                    guild_roles_list.splice(i, 1);
                    return;
                }
            }
        });
        
        socket.on("channel_list", function (chans) {
            fill_channels(chans);
            for (var i = 0; i < chans.length; i++) {
                var thischan = chans[i];
                if (thischan.channel.id == selected_channel) {
                    $("#channeltopic").text(thischan.channel.topic);
                }
            }
        });
        
        socket.on("current_user_info", function (usr) {
            update_embed_userchip(true, usr.avatar, usr.username, usr.nickname, usr.userid, usr.discriminator);
        });
        
        socket.on("lookup_user_info", function (usr) {
            var key = usr.name + "#" + usr.discriminator;
            var cache = message_users_cache[key];
            if (!cache) {
                return;
            }
            cache["data"] = usr;
            process_message_users_cache_helper(key, usr);
        });
        
        socket.on("guest_icon_change", function (icon) {
            global_guest_icon = icon.guest_icon;
        });
        
        socket.on("ack", function () {
            socket_last_ack = moment();
            if (socket && socket_error_should_refetch) {
                run_fetch_routine();
            }
        });
    }
    
    function update_socket_channels() {
        if (!socket) {
            return;
        }
        socket.emit("channel_list", {"guild_id": guild_id, "visitor_mode": visitor_mode});
    }
    
    function send_socket_heartbeat() {
        if (socket_last_ack) {
            var now = moment();
            var duration = moment.duration(now.diff(socket_last_ack)).minutes();
            if (socket && duration >= 1) { // server must hanged, lets reconnect
                socket_error_should_refetch = true;
                socket.disconnect();
                socket = null;
                initiate_websockets();
            }
        }
        
        if (socket) {
            socket.emit("heartbeat", {"guild_id": guild_id, "visitor_mode": visitor_mode});
        }
    }
})();

function submit_unauthenticated_captcha() { // To be invoked when recaptcha is completed
    $('#recaptchamodal').modal('close');
    $("#submit-unauthenticated-captcha-btn").click();
}

window._3rd_party_test_step1_loaded = function () {
    // At this point, a third-party domain has now attempted to set a cookie (if all went to plan!)
    var step2El = document.createElement('script');
    // And load the second part of the test (reading the cookie)
    step2El.setAttribute('src', cookie_test_s2_URL);
    document.getElementById("third-party-cookies-notice").appendChild(step2El);
};

window._3rd_party_test_step2_loaded = function (cookieSuccess) {
    if (!cookieSuccess) {
        $("#third-party-cookies-notice").show().addClass("done");
        $("#login-greeting-msg, #loginmodal-maincontent").hide();
    } else {
        $("#third-party-cookies-notice").hide().addClass("done");
        $("#login-greeting-msg, #loginmodal-maincontent").show();
    }
};

window.setTimeout(function(){
    var noticeDiv = $("#third-party-cookies-notice");
    if (!noticeDiv.hasClass("done")) {
        window._3rd_party_test_step2_loaded(false);
    }
}, 7*1000);

$("#third-party-cookies-force-hide").click(function () {
    window._3rd_party_test_step2_loaded(true);
});

$("#third-party-cookies-force-window").click(function () {
    window.open(window.location.href);
});
