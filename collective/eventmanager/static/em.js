(function($){
$(document).ready(function(){

    setTimeout(function(){
        // need to wait for maps to get setup...
        var map = $('#map');

        if(map.length > 0){
            map.hide();
            var btn = $('<a id="map-btn" href="#">Show Map</a>');
            map.before(btn);
            btn.click(function(){
                if(!btn.hasClass('open')){
                    btn.addClass('open');
                    btn.html("Hide Map");
                    map.slideDown();
                }else{
                    map.slideUp();
                    btn.html("Show Map");
                    btn.removeClass('open');
                }
                return false;
            });

        }
    }, 1000);
});
})(jQuery);