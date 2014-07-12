(function ($) {
    $(document).ready(function () {
        if (document.location.href.indexOf('/add/') == -1) {
            if ($('#searchbar').length == 0 && $('#grp-changelist-search').length == 0) {
                var test_button = '<li><a href="./sendmail/" class="historylink">Test template</a></li>';
                if ($('.object-tools').length == 1) {
                    $('.object-tools').append(test_button);
                }
                else if ($('.grp-object-tools').length == 1) {
                    $('.grp-object-tools').append(test_button);
                }
                ;
            }
            ;
        }
        ;
    });
})(django.jQuery);
