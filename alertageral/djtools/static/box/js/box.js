$(document).ready(function(){
	$("div.box > input[name=expansible]").each(function() {
		if ($(this).val() == 'True') {
			$(this).parent().find("h3.title").css('cursor','pointer');
		}
	})
	
	$("div.box > h3.title").click(function() {
	  elem = $(this);
	  if (elem.parent().find('input[name=expansible]').val() == 'True') {
	  	if (elem.next().is(":visible")) {
	  		elem.next().hide('fast');
	  		elem.find("img").attr("src", "/static/djtools/box/img/plus.png");
	  	}
	  	else {
	  		elem.next().show('fast');
	  		elem.find("img").attr("src", "/static/djtools/box/img/minus.png");
	  	}
	  }
	})
	
	// omite a caixa com informações
	el = $("div.box > h3.collapsed").next().css('display','none');
})