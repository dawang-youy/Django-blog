/*===  navMenuStart ===*/
window.onload = function(){
    let navId = $('#header .nav .menu').data('navid')
    //console.log(navId)
    //console.log( $('#header .nav .menu').eq(navId))
    $('#header .nav .menu li').eq(navId).addClass('active')
    // .siblings('li').removeClass('active')
};
/*===  navMenuEnd ===*/
