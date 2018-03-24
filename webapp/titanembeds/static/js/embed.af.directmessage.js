(function () {
    /* global $, Mustache, soundManager, Materialize */
    
    const MODAL_TEMPLATE = `
        <div id="af_dm_modal" class="modal">
          <div class="modal-content">
            <h4 class="center-align">Direct Messaging: <span class="username">EndenDragon</span><span class="hash">#</span><span class="discriminator">1337</span></h4>
            <div class="dmcontent" style="background-color: rgba(0, 0, 0, 0.1); min-height: 150px; height: 50vh; overflow-y: scroll; padding: 10px;"></div>
            <div class="row" style="background-color: rgba(255, 255, 255, 0.2); padding-left: 4px; padding-right: 4px;">
                <div class="input-field inline" style="width: 100%; height: 27px;">
                    <input id="af_dm_msgbox" placeholder="Message user">
                </div>
            </div>
          </div>
        </div>
    `;
    
    const MESSAGE_TEMPLATE = `
        <div style="border-top: solid 1px rgba(0, 0, 0, 0.1); padding-top: 5px;">
            <img class="authoravatar" src="{{ avatar }}">
            <span class="chatusername"><span class="authorname">{{ username }}</span><span class="authorhash">#</span><span class="authordiscriminator">{{ discriminator }}</span></span>
            <span class="chatmessage">{{ message }}</span>
        </div>
    `;
    
    var notification_sound = soundManager.createSound({
        id: 'notification_sound_id',
        url: "/static/audio/demonstrative.mp3",
        volume: 8,
    });
    
    var dmStorage = {}; // {"EndenDragon#1337": {cs: "code", conversation: [{me: true, message: "stuff"}, ...]}, ...}
    
    function cleverJax(cs, input) {
        var data = {"input": input};
        if (cs) {
            data.cs = cs;
        }
        var funct = $.ajax({
            method: "POST",
            dataType: "json",
            url: "/api/af/direct_message",
            data: data
        });
        return funct.promise();
    }
    
    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
    
    function getID(user) {
        return user.username + "#" + user.discriminator;
    }
    
    function getCS(id) {
        if (!dmStorage[id]) {
            return null;
        }
        return dmStorage[id].cs;
    }
    
    function setCS(id, cs) {
        if (!dmStorage[id]) {
            createDM(id);
        }
        dmStorage[id].cs = cs;
    }
    
    function createDM(id) {
        dmStorage[id] = {
            cs: null,
            conversation: [],
        };
    }
    
    function populateDM(id) {
        $("#af_dm_modal .dmcontent").empty();
        if (!dmStorage[id]) {
            createDM(id);
        }
        var msgs = dmStorage[id].conversation;
        for (var i = 0; i < msgs.length; i++) {
            var user;
            if (msgs[i].me) {
                user = getMySelfUser();
            } else {
                user = getCurrentUser();
            }
            var rendered = Mustache.render(MESSAGE_TEMPLATE, {
                avatar: user.avatar,
                username: user.username,
                discriminator: user.discriminator,
                message: msgs[i].message
            });
            $("#af_dm_modal .dmcontent").append(rendered);
        }
    }
    
    function addMessage(id, me, message) {
        if (!dmStorage[id]) {
            createDM(id);
        }
        dmStorage[id].conversation.push({
            me: me,
            message: message
        });
        populateDM(id);
    }
    
    function getMySelfUser() {
        var username = $("#curuser_name").text();
        var discriminator = $("#curuser_discrim").text();
        var avatar = $("#currentuserimage").attr("src");
        return {
            "username": username,
            "discriminator": discriminator,
            "avatar": avatar,
        };
    }
    
    function getCurrentUser() {
        var username = $("#usercard .identity .username").text();
        var discriminator = $("#usercard .identity .discriminator").text();
        var avatar = $("#usercard .avatar").attr("src");
        return {
            "username": username,
            "discriminator": discriminator,
            "avatar": avatar,
        };
    }
    
    function sendDM(value) {
        var id = getID(getCurrentUser());
        var cs = getCS(id);
        var cj = cleverJax(cs, value);
        addMessage(id, true, value);
        cj.done(function (data) {
            setCS(id, data.cs);
            setTimeout(function () {
                addMessage(id, false, data.output);
                if (notification_sound.playState == 0) {
                    notification_sound.play();
                }
            }, getRandomInt(2000, 3500));
        });
    }
    
    function openDM() {
        var curUser = getCurrentUser();
        $("#af_dm_modal h4 .username").text(curUser.username);
        $("#af_dm_modal h4 .discriminator").text(curUser.discriminator);
        populateDM(getID(curUser));
        $('#af_dm_modal').modal('open');
    }
    
    $(function() {
        $(MODAL_TEMPLATE).insertAfter("#usercard").modal({
            dismissible: true,
        });
        var openDMbtn = $("<a class=\"waves-effect waves-light btn orange\" id=\"openDM\">DM User</a>");
        openDMbtn.bind("click", openDM);
        openDMbtn.insertAfter("#usercard-mention-btn");
        $("#af_dm_msgbox").bind("keyup", function (e) {
            if (e.which == 13) {
                e.preventDefault();
                sendDM($("#af_dm_msgbox").val());
                $("#af_dm_msgbox").val("");
                $("#af_dm_msgbox").focus();
            }
        });
        Mustache.parse(MESSAGE_TEMPLATE);
        Materialize.toast('We now support Direct Messages! Click on a username in chat/sidebar to start sending message directly to each other.', 5000);
    });
})();