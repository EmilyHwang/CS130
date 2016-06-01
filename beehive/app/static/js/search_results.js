// Process Asynchornous request

$(function() {
	$('form.results').on('submit', function (e) {
		e.stopPropagation();
		e.preventDefault();

		$.ajax({
			type: 'POST',
			url: '/follow',
			data: $(this).serialize(),
			success: function(response) {
				if ($(e.currentTarget).find('input[name="followStatus"]').val() == 'True') {
					$(e.currentTarget).children('button.unfollow-btn').toggleClass('unfollow-btn follow-btn');
					$(e.currentTarget).children('button.follow-btn').text('Follow');
				} else {
					$(e.currentTarget).children('button.follow-btn').toggleClass('follow-btn unfollow-btn');
					$(e.currentTarget).children('button.unfollow-btn').text('Unfollow');
				}
			}, 
			error: function(error) {
			}

		})
	});
});