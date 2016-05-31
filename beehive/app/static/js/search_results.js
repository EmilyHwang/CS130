// Process Asynchornous request

$(function() {
	$('form').on('submit', function (e) {
		e.stopPropagation();
		e.preventDefault();

		$.ajax({
			type: 'POST',
			url: '/follow',
			data: $(this).serialize(),
			success: function(response) {				
				$(e.currentTarget).children('button.follow-btn').toggleClass('follow-btn unfollow-btn');
				$(e.currentTarget).children('button.unfollow-btn').text('Unfollow');
			}, 
			error: function(error) {
				alert(error);
			}

		})
	});
});