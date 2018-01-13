/*global $, ace, Materialize, newCSS, CSS_ID, ADMIN*/
(function () {
    if($("#css_editor").length != 0) {
        var editor = ace.edit("css_editor");
    }
    
    function postForm() {
        var name = $('#css_name').val();
        var var_enabled = $("#toggleCSSVar").is(':checked');
        var css = null;
        if($("#css_editor").length != 0) {
            css = editor.getValue();
            if (css.length == 0) {
                css = null;
            }
        }
        
        var payload = {"name": name, "variables_enabled": var_enabled, "css": css};
        if (var_enabled) {
            var variables = JSON.stringify(formatCSSVars());
            payload.variables = variables;
        }
        if (ADMIN) {
            var user_id = $('#css_user_id').val();
            payload.user_id = user_id;
        }
        
        var funct = $.ajax({
            dataType: "json",
            method: "POST",
            data: payload
        });
        return funct.promise();
    }
    
    $(function(){
        if($("#css_editor").length != 0) {
            editor.getSession().setMode("ace/mode/css");
            editor.setTheme("ace/theme/chrome");
            
            editor.commands.addCommand({
                name: 'save',
                bindKey: {win: "Ctrl-S", "mac": "Cmd-S"},
                exec: function(editor) {
                    $('#submit-btn').trigger('click');
                }
            });
            editor.on("blur", function () {
                update_live_preview();
            });
        }
        $("#submit-btn").click(submitForm);
        
        if (!newCSS) {
            $("#delete-btn").click(delete_css);
        }
        
        $(".updateLivePreview").on("blur", function () {
            update_live_preview();
        });
        
        $("#toggleCSSVar").on("change", function () {
            update_live_preview();
        });
        
        $("#preview_guildid").keyup(function (event) {
            if (event.keyCode == 13) {
                change_live_preview();
            }
        });
    });
    
    function formatCSSVars() {
        return {
            "modal": $("#css_var_modal").val(),
            "noroleusers": $("#css_var_noroleusers").val(),
            "main": $("#css_var_main").val(),
            "placeholder": $("#css_var_placeholder").val(),
            "sidebardivider": $("#css_var_sidebardivider").val(),
            "leftsidebar": $("#css_var_leftsidebar").val(),
            "rightsidebar": $("#css_var_rightsidebar").val(),
            "header": $("#css_var_header").val(),
            "chatmessage": $("#css_var_chatmessage").val(),
            "discrim": $("#css_var_discrim").val(),
            "chatbox": $("#css_var_chatbox").val(),
        };
    }
    
    function submitForm() {
        var name = $('#css_name').val();
        if (name == "") {
            Materialize.toast("Don't forget to name your CSS!", 10000);
            return;
        }
        
        var formPost = postForm();
        formPost.done(function (data) {
            if (newCSS) {
                window.location.href = "edit/" + data.id;
            } else {
                Materialize.toast('CSS Updated!', 10000);
                update_live_preview(true);
                $("#live_preview_warning").hide();
            }
        });
        formPost.fail(function () {
            Materialize.toast('Oh no! Something has failed posting your CSS!', 10000);
        });
    }

    function delete_css() {
        var candelete = confirm("Do you really want to delete this css???");
        if (!candelete) {
            return;
        }
        
        $.ajax({
          type: 'DELETE',
          success: function() {
              alert("You have successfully deleted the CSS!");
                    if (ADMIN) {
                        window.location.href = "/admin/custom_css";
                    } else {
                        window.location.href = "/user/dashboard";
                    }
              },
          error: function() {
              Materialize.toast('Oh no! Something has failed deleting your CSS!', 10000);
          }
        });
    }
    
    function update_live_preview(refresh=false) {
        if (refresh) {
            $('#iframepreview').attr('src', $('#iframepreview').attr('src'));
            return;
        }
        $("#live_preview_warning").show();
        var output = "";

        if ($("#toggleCSSVar").is(':checked')) {
            var cssVars = formatCSSVars();
            output += ":root {";
            for (var key in cssVars) {
              if (cssVars.hasOwnProperty(key)) {
                output += "--" + key + ":" + cssVars[key] + ";";
              }
            }
            output += "}";
        }
        
        if($("#css_editor").length != 0) {
            output += editor.getValue();
        }
        
        $("#iframepreview").contents().find('#user-defined-css').html(output);
    }
    
    function change_live_preview() {
        var src = "/embed/" + $("#preview_guildid").val();
        if (!newCSS) {
            src += "?css=" + CSS_ID;
        }
        $("#iframepreview").attr("src", src);
        update_live_preview();
    }
})();