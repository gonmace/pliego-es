/**
 * Main
 */


/** Once Page is Loaded */
$(document).ready(function(){

    $('#spinner').fadeIn('slow');

    $('#content').load(''); 
    $("ul.list-unstyled li").first().addClass("active");

    $('#spinner').fadeOut('slow');

});

/** Once Selected Another Side Menu, Load It */
$(document).on('click', ".side-menu", function(event) {

    event.preventDefault();

    // Remove 'Active' class from Side Menu
    $("ul.list-unstyled li").removeClass("active");

    // Load Side Menu Selected
    var menu = $(this).attr('id');

      $('#content').load(menu);

      // Add 'Active' Class to Selected Menu
      $(this).parent().addClass("active");

});

/** Logout */
$(document).on('click', "#logout", function(event) {

    event.preventDefault();
    
    localStorage.clear();
    setTimeout('window.location.href = "index";',300);

});