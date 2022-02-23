
$(document).ready(function(){

    // console.log('property_website_rpc----------', property_website_rpc);
    $(".heart").on("click", function() {
    $(this).toggleClass("is-active");
  });

    
	// Lift card and show stats on Mouseover
	$('#property-card').hover(function(){
			$(this).addClass('animate');
			$('div.carouselNext, div.carouselPrev').addClass('visible');
		 }, function(){
			$(this).removeClass('animate');
			$('div.carouselNext, div.carouselPrev').removeClass('visible');
	});
    //code for click on property name then redirect property page


});
