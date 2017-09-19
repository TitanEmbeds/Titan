/*global $, ace, Materialize, newCSS, CSS_ID*/
(function () {
    if($("#css_editor").length != 0) {
        var editor = ace.edit("css_editor");
    }
    
    function postForm() {
        var name = $('#css_name').val();
        var var_enabled = $("#toggleCSSVar").is(':checked');
        var variables = JSON.stringify(formatCSSVars());
        var css = null;
        if($("#css_editor").length != 0) {
            css = editor.getValue();
            if (css.length == 0) {
                css = null;
            }
        }
        var funct = $.ajax({
            dataType: "json",
            method: "POST",
            data: {"name": name, "variables_enabled": var_enabled, "variables": variables, "css": css}
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
              window.location.href = "/user/dashboard";
          },
          error: function() {
              Materialize.toast('Oh no! Something has failed deleting your CSS!', 10000);
          }
        });
    }
    
    function update_live_preview(refresh=false) {
        if (refresh) {
            $('#iframepreview')[0].contentWindow.location.reload(true);
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