$('.carousel .carousel-item').each(function() {
      var next = $(this).next();
      if (!next.length) {
      next = $(this).siblings(':first');
      }
      next.children(':first-child').clone().appendTo($(this));
      
      for (var i=0;i<2;i++) {
          next=next.next();
          if (!next.length) {
              next = $(this).siblings(':first');
            }
          
          next.children(':first-child').clone().appendTo($(this));
        }
});

$(document).ready(function() {
  $(".library_recipe").addClass('onload');
})



$('input[name=cuisines]').on('change', () => {
  $(".library_recipe").removeClass('onload');
  let tagArray = []

  checkedArray = []

  checked = $('input[name=cuisines]:checked')
  for (x of checked) {
    checkedArray.push(x.id)
  }

  $allRecipes = $("#all_recipes")[0].children
  

  for (card of $allRecipes) {
    let show;
    tagList = card.firstElementChild.children[1].children[0].children[2].children
   for (span of tagList) {
     tagArray.push(span.className)
   }
   for (tag of tagArray) {
    if (checkedArray.includes(tag)) {
      show = true
    }  else {
      if (show != true) {
        show = false
      }
       else {
         show = true
       }
    }
    console.log(tag, checkedArray, show)
   }
   tagArray = []
   console.log('finished a card')
   if (show === true) {
     console.log('running true')
    cardID = card.id
    $(`#${cardID}`).addClass('showCard')
    $(`#${cardID}`).removeClass('hideCard')
    show=false
  } else {
    console.log('running false')

    cardID = card.id
    $(`#${cardID}`).removeClass('showCard')
    $(`#${cardID}`).addClass('hideCard')
  }

   
  
}
})

$recipe_summary = $(".recipe-summary");
function strip_html_tags_summary(str) {
   if ((str===null) || (str==='')) 
       return false;
  else
  str = str.toString();
  str.replace(/<[^>]*>/g, '');
  str.replace(/^Summary: $/, '')
  $recipe_summary.empty()
  return $recipe_summary.append(`<b>Summary: </b> ${str}`)
}
str = $recipe_summary[0].innerText;
strip_html_tags_summary(str)


$recipe_directions = $('#recipe-directions')
str2 = $recipe_directions[0].innerText
function strip_html_tags_directions(str2) {
  if ((str2===null) || (str2===''))
      return false;
 else
  str2 = str2.toString();
 str2.replace(/<[^>]*>/g, '');
 $recipe_directions.empty();
 return $recipe_directions.append(str2)
}
$('#directions-tab').click(strip_html_tags_directions(str2))


$('#servingMeasure input').on('change', function() {
  $servingMeasure = $('input[name=inlineRadioOptions]:checked', '#servingMeasure').val();

 if (!$servingMeasure || $servingMeasure === 'US') {
    $('#us').show();
    $('#metric').hide();
  } else if ($servingMeasure === 'Metric') {
  $('#metric').show();
  $('#us').hide();
  } 
});


if(window.location.hash) {
  var hash = window.location.hash;
  $(hash).modal('toggle');
}
