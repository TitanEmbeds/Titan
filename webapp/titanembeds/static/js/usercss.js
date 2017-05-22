/*global $, ace, Materialize, newCSS*/
(function () {
    var editor = ace.edit("css_editor");
    
    function postForm() {
        var name = $('#css_name').val();
        var css = editor.getValue();
        var funct = $.ajax({
            dataType: "json",
            method: "POST",
            data: {"name": name, "css": css}
        });
        return funct.promise();
    }
    
    $(function(){
        editor.getSession().setMode("ace/mode/css");
        editor.setTheme("ace/theme/chrome");
        $("#submit-btn").click(submitForm);
        
        if (!newCSS) {
            $("#delete-btn").click(delete_css);
        }
    });
    
    function submitForm() {
        var formPost = postForm();
        formPost.done(function (data) {
            if (newCSS) {
                window.location.href = "edit/" + data.id;
            } else {
                Materialize.toast('CSS Updated!', 10000);
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
})();