(function($){
$(document).ready(function(){
    var map = $('#map');

    if(map.length > 0){
        var btn = $('<a id="map-btn" href="#" class="open">Hide Map</a>');
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
});
})(jQuery);
