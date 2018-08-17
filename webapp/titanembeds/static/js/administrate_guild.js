$('.chips').material_chip();
$('select').material_select();

$('#unauth_users').change(function() {
    var pathname = window.location.pathname;
    var checked = $(this).is(':checked')
    var payload = {"unauth_users": checked}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated guest users setting!', 2000)
    });
});

$('#visitor_view').change(function() {
    var pathname = window.location.pathname;
    var checked = $(this).is(':checked')
    var payload = {"visitor_view": checked}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated visitor mode setting!', 2000)
    });
});

$('#webhook_messages').change(function() {
    var pathname = window.location.pathname;
    var checked = $(this).is(':checked')
    var payload = {"webhook_messages": checked}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated webhook messages setting!', 2000)
    });
});

$('#chat_links').change(function() {
    var pathname = window.location.pathname;
    var checked = $(this).is(':checked')
    var payload = {"chat_links": checked}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated chat links setting!', 2000)
    });
});

$('#bracket_links').change(function() {
    var pathname = window.location.pathname;
    var checked = $(this).is(':checked')
    var payload = {"bracket_links": checked}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated embed links setting!', 2000)
    });
});

$("#mentions_limit").keyup(function(event){
    if(event.keyCode == 13){
      var pathname = window.location.pathname;
      var value = $("#mentions_limit").val()
      var payload = {"mentions_limit": value}
      $.post(pathname, payload, function(data) {
        Materialize.toast('Updated mentions limit setting!', 2000)
      });
    }
});

$("#post_timeout").keyup(function(event){
    if(event.keyCode == 13){
      var pathname = window.location.pathname;
      var value = $("#post_timeout").val()
      var payload = {"post_timeout": value}
      $.post(pathname, payload, function(data) {
        Materialize.toast('Updated post timeout setting!', 2000)
      });
    }
});

$("#max_message_length").keyup(function(event){
    if(event.keyCode == 13){
      var pathname = window.location.pathname;
      var value = $("#max_message_length").val()
      var payload = {"max_message_length": value}
      $.post(pathname, payload, function(data) {
        Materialize.toast('Updated max message length setting!', 2000)
      });
    }
});

$("#invite_link").keyup(function(event){
    if(event.keyCode == 13){
      var pathname = window.location.pathname;
      var value = $("#invite_link").val()
      var payload = {"invite_link": value}
      $.post(pathname, payload, function(data) {
        Materialize.toast('Updated invite link setting!', 2000)
      });
    }
});

$("#guest_icon").keyup(function(event){
    if(event.keyCode == 13){
      var pathname = window.location.pathname;
      var value = $("#guest_icon").val()
      var payload = {"guest_icon": value}
      $.post(pathname, payload, function(data) {
        Materialize.toast('Updated Guest Icon setting!', 2000)
      });
    }
});

$('#unauth_captcha').change(function() {
    var pathname = window.location.pathname;
    var checked = $(this).is(':checked')
    var payload = {"unauth_captcha": checked}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated Guest User Captcha setting!', 2000)
    });
});

$('#banned_words_enabled').change(function() {
    var pathname = window.location.pathname;
    var checked = $(this).is(':checked')
    var payload = {"banned_words_enabled": checked}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated Banned Words setting!', 2000)
    });
});

$('#banned_words_global_included').change(function() {
    var pathname = window.location.pathname;
    var checked = $(this).is(':checked')
    var payload = {"banned_words_global_included": checked}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated Banned Words Global setting!', 2000)
    });
});

var banned_words_data = [];
for (var i = 0; i < BANNED_WORDS.length; i++) {
  banned_words_data.push({
    tag: BANNED_WORDS[i]
  });
}

$('#banned_words').material_chip({
  data: banned_words_data,
});

$('#banned_words').on('chip.add', function(e, chip){
  add_delete_banned_words("add", chip.tag);
});

$('#banned_words').on('chip.delete', function(e, chip){
  add_delete_banned_words("delete", chip.tag);
});

function add_delete_banned_words(action, word) {
    var pathname = window.location.pathname;
    var payload = {"banned_word": word, "delete_banned_word": action == "delete"}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated Banned Words list!', 2000)
    });
}

$("#autorole_unauth").change(function () {
    var pathname = window.location.pathname;
    var value = $(this).val();
    var payload = {"autorole_unauth": value}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated Guest AutoRole setting!', 2000)
    });
});

$("#autorole_discord").change(function () {
    var pathname = window.location.pathname;
    var value = $(this).val();
    var payload = {"autorole_discord": value}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated Discord AutoRole setting!', 2000)
    });
});

$('#file_upload').change(function() {
    var pathname = window.location.pathname;
    var checked = $(this).is(':checked')
    var payload = {"file_upload": checked}
    $.post(pathname, payload, function(data) {
      Materialize.toast('Updated file uploads setting!', 2000)
    });
});

function initiate_ban(guild_id, user_id) {
  var reason = prompt("Please enter your reason for ban");
  var payload = {
    "reason": reason,
    "guild_id": guild_id,
    "user_id": user_id,
  }
  var pathname = document.location.origin + "/user/ban"

  if (reason != null) {
    $.post(pathname, payload)
      .done(function(){
        location.reload();
      })
      .fail(function(xhr, status, error) {
        if (error == "CONFLICT") {
          Materialize.toast('User is already banned!', 2000)
        } else {
          Materialize.toast('An error has occured!', 2000)
        }
      });
  }
}

function remove_ban(guild_id, user_id) {
  var payload = {
    "guild_id": guild_id,
    "user_id": user_id,
  }
  var pathname = document.location.origin + "/user/ban"

  $.ajax({
      url: pathname + '?' + $.param(payload),
      type: 'DELETE',
      success: function() {
        location.reload();
      },
      error: function(jqxhr, status, error) {
        if (error == "CONFLICT") {
          Materialize.toast('User is already pardoned!', 2000)
        } else {
          Materialize.toast('An error has occured!', 2000)
        }
      }
  });
}

function revoke_user(guild_id, user_id) {
  var payload = {
    "guild_id": guild_id,
    "user_id": user_id,
  }
  var confirmation = confirm("Are you sure that you want to kick user?")
  var pathname = document.location.origin + "/user/revoke"
  if (confirmation) {
    $.post(pathname, payload)
      .done(function(){
        location.reload();
      })
      .fail(function(xhr, status, error) {
        if (error == "CONFLICT") {
          Materialize.toast('User is already revoked!', 2000)
        } else {
          Materialize.toast('An error has occured!', 2000)
        }
      });
  }
}
