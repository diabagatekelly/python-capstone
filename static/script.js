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



$('input[type=checkbox]').on('change', () => {
checkedArray = []

checked = $('input[type=checkbox]:checked')
for (x of checked) {
checkedArray.push(x.id)
}


if (checkedArray.length !=0) {
$(".library_recipe").removeClass('onload');
let tagArray = []
$allRecipes = $("#all_recipes")[0].children

for (card of $allRecipes) {
  console.log(card)
  let show;
  cuisineTagList = card.firstElementChild.children[1].children[0].children[2].children
  dietTagList = card.firstElementChild.children[1].children[0].children[3].children
  customTagList = card.firstElementChild.children[1].children[0].children[4].children
  source = card.firstElementChild.id
  console.log(source)
 for (span of cuisineTagList) {
   tagArray.push(span.className)
 }
 for (span of dietTagList) {
  tagArray.push(span.className)
}
for (span of customTagList) {
  tagArray.push(span.className)
}
tagArray.push(source)

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
 }
 tagArray = []
 if (show === true) {
  cardID = card.id
  $(`#${cardID}`).addClass('showCard')
  $(`#${cardID}`).removeClass('hideCard')
  show=false
} else {  
  cardID = card.id
  $(`#${cardID}`).removeClass('showCard')
  $(`#${cardID}`).addClass('hideCard')
}
}
$showingNum = $('.showCard')
$('#showingNum').html($showingNum.length)

} else {
$(".library_recipe").addClass('onload');
$(`#${cardID}`).removeClass('hideCard')
$(`#${cardID}`).removeClass('showCard')

$showingNum = $('.onload')
$('#showingNum').html($showingNum.length)
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
