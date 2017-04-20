(function ($) {
    $(document).ready(function () {
        if (document.location.href.indexOf('/add/') == -1) {
            if ($('#searchbar').length == 0 && $('#grp-changelist-search').length == 0) {
                var test_button = '<li><a href="javascript:void(0);" onclick="test_app_template();" class="historylink">Test template</a></li>';
                var browse_button = '<li><a href="javascript:void(0);" onclick="show_apps_dialog();" class="historylink" target="_blank">Browse vars</a></li>';
                if ($('.object-tools').length == 1) {
                    $('.object-tools').append(test_button);
                    $('.object-tools').append(browse_button);
                }
                else if ($('.grp-object-tools').length == 1) {
                    $('.grp-object-tools').append(test_button);
                    $('.grp-object-tools').append(browse_button);
                }
            }
        }

        test_app_template = function () {
            location.href = document.location.href.replace('change/', '') + 'sendmail/';
        };

        show_apps_dialog = function () {
            var appUrl = document.location.href.replace('change/', '') + 'sendmail/apps/';
            $(
                '<div><iframe src="'+appUrl+'" width="100%" height="100%"></iframe></div>'
            ).dialog({
                    modal: true,
                    draggable: true,
                    height: 500,
                    width: 350,
                    resizable: true
                }
            ).position({
                    my: "center",
                    at: "center",
                    of: window
                }
            ).show()
            ;
        }
        ;
    });
})((typeof(grp) == "undefined") ? django.jQuery : grp.jQuery);
