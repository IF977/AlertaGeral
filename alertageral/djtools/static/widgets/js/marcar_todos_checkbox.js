$(document).ready(function(){
	$('.checkbutton').click(function () {
		var campo = $(this).attr("data-elemento");
		if ($(this).hasClass("markall")) {
			var checked = true;
			$(this).removeClass("markall");
			$(this).text("Desmarcar Todos");
		} else {
			var checked = false;
			$(this).addClass("markall");
			$(this).text("Marcar Todos");
		}
		$('input[name="'+campo+'"]').each(function(){
			if (checked) {
				$(this).attr('checked', 'checked');	
			} else {
				$(this).removeAttr('checked')
			}
		});	
		return false	
	});
});
