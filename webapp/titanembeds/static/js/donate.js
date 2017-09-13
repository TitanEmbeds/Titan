/* global $, location, Materialize */
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
    
    function patchForm(item, amount) {
        var funct = $.ajax({
            dataType: "json",
            method: "PATCH",
            data: {"item": item, "amount": amount},
        });
        return funct.promise();
    }
    
    $("#buy-custom-css-slots-btn").click(function () {
        var amount = $.trim($("#custom-css-slots-amount").val());
        if (amount == "") {
            return;
        }
        var formPatch = patchForm("custom_css_slots", amount);
        formPatch.done(function (data) {
            alert("Successfully bought " + amount + " custom css slots!");
            location.reload();
        });
        formPatch.fail(function (data) {
            if (data.status == 400) {
                Materialize.toast('Amount cannot be zero or under!', 10000);
            } else if (data.status == 402) {
                Materialize.toast('Insufficient token funds!', 10000);
            } else {
                Materialize.toast('Purchasing custom css slots failed!', 10000);
            }
        });
    });

    $("#buy-webhook-guest-user-avatar-btn").click(function () {
        var formPatch = patchForm("webhook_icon", 1);
        formPatch.done(function (data) {
            alert("Successfully bought webhook guest user avatar perk!");
            location.reload();
        });
        formPatch.fail(function (data) {
            if (data.status == 400) {
                Materialize.toast('Item already purchased!', 10000);
            } else if (data.status == 402) {
                Materialize.toast('Insufficient token funds!', 10000);
            } else {
                Materialize.toast('Purchasing webhook guest user avatar perk failed!', 10000);
            }
        });
    });
})();