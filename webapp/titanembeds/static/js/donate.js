/* global $ */
(function () {
    $('#token-slider').on('input', function(){
        var slider_value = $("#token-slider").val();
        var multiplier = 100;
        
        $("#money-display").text(slider_value);
        $("#token-display").text(slider_value * multiplier);
    });
    
    $("#donate-btn").click(function () {
        var slider_value = $("#token-slider").val();
        var form = $('<form method="POST">' + 
            '<input type="hidden" name="amount" value="' + slider_value + '">' +
            '</form>');
        $(document.body).append(form);
        form.submit();
    });
})();