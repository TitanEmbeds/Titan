/* global $ */
(function () {
    $(function() {
        $(".brand-logo").html($(".brand-logo").html().replace(/Titan/g,'Sausage'));
        $(".brand-logo .betatag").text("ALPHA");
        try {
            $("main > .container").html($("main > .container").html().replace(/Titan/g,'Sausage'));
            $("#dblbanner").html($("#dblbanner").html().replace(/Titan/g,'Sausage'));
        } catch (e) {
            // nothing
        }
        $("nav .brand-logo img").attr("src", "https://i.imgur.com/6xPdXFV.png");
    });
})();