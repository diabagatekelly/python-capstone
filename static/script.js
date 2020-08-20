$('.carousel .carousel-item').each(function(){
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
  console.log(str2)
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
console.log($servingMeasure);

 if (!$servingMeasure || $servingMeasure === 'US') {
    $('#us').show();
    $('#metric').hide();
  } else if ($servingMeasure === 'Metric') {
  $('#metric').show();
  $('#us').hide();
  } 
});