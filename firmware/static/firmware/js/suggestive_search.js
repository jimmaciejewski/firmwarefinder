const search_box = $("#search-box")
const spinner = $('#spinner')
const product_div = $('#products-div')
const endpoint = '/products-search'
const delay_by_in_ms = 700

const data = document.currentScript.dataset;
const link = data.link;


let scheduled_scroll = false
let scheduled_function = false

var discontinued = false
if (window.location.pathname === '/discontinued-products') {
	discontinued = true
}

let ajax_call = function (endpoint, request_parameters) {
	$.getJSON(endpoint, request_parameters)
		.done(response => {
			product_div.html(response['html_from_view'])
			spinner.hide()
			product_div.fadeIn()
			$('.firmwares').click(function(e){
				// Don't act on clicks in read_me
				e.stopPropagation()
				return
			})
			
			$('.readme').click(function(e){
				// Don't act on clicks in read_me
				e.stopPropagation()
				return
			})

			$('.download-button').click(function(e) {
				//Stop here so we don't open readme
				e.stopPropagation()
				return
			})
	  
			$('.expandable-box').click(function(e) {
				if($(this).hasClass('open')) {
					// Contract
					$('.expandable-box.out').not($(this)).removeClass('out');
					$(this).removeClass('open');
					$(this).find('.firmwares').addClass('hidden');
					$(this).addClass('last-clicked')
		
				} else if($(this).hasClass('out')) {
					// console.log("Clicked on something that is hidden");
					return
				} else {
					// Expand
					$(this).find('.firmwares').removeClass('hidden')
					$('.expandable-box').not($(this)).addClass('out');
					$('.expandable-box').removeClass('last-clicked')
					$(this).addClass('open');
				}
				if (scheduled_scroll) {
					clearTimeout(scheduled_scroll)
				}
			
				// setTimeout returns the ID of the function to be executed

				const yOffset = -150; 
				const y = $(this)[0].getBoundingClientRect().top + window.pageYOffset + yOffset;

				
				scheduled_scroll = setTimeout(window.scrollTo({top: y, behavior: 'smooth'}), 1000)
				
			});

			if(link != 'None'){
				$('.product[title="' + link + ' "]').click()
			}

			$('.readme-button').click(function(e) {
				$(this).find('.readme').toggle()
			});
		})
}


search_box.on('keyup', function () {

	const request_parameters = {
		q: $(this).val() // value of user_input: the HTML element with ID user-input
	}
	request_parameters['discontinued'] = discontinued

	// start animating the search icon with the CSS class
	product_div.fadeOut()
	spinner.fadeIn()

	// if scheduled_function is NOT false, cancel the execution of the function
	if (scheduled_function) {
		clearTimeout(scheduled_function)
	}

	// setTimeout returns the ID of the function to be executed
	scheduled_function = setTimeout(ajax_call, delay_by_in_ms, endpoint, request_parameters)
})

$(document).ready(function () {
	const request_parameters = {'discontinued': discontinued}
	ajax_call(endpoint, request_parameters)
})