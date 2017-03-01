(function ($) {
    $(document).ready(function () {
        base_url = $(location). attr("href").replace("change/", '');
        $('#wrap').append('<iframe id="frame" src="" width="100%" height="300"> </iframe>');

        if (document.location.href.indexOf('/add/') == -1) {
            if ($('#searchbar').length == 0 && $('#grp-changelist-search').length == 0) {
                var test_button = '<li><a href="'+base_url+'sendmail/" class="historylink">Test template</a></li>';
                var browse_button = '<li><a href="'+base_url+'sendmail/apps" target="blank" class="historylink" target="_blank">Browse vars</a></li>';
                $('.menu-box').append(test_button);
                $('.menu-box').append(browse_button);
            };
        };

    });
})((typeof(grp) == "undefined") ? django.jQuery : grp.jQuery);
