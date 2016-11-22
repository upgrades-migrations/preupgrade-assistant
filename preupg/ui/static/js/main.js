$(document).ready(function(){
  $('.selectpicker').selectpicker();
});

/* fix height of left column when displaying test result
 * flex grid layout could be used but is not really supported ATM
 */
function fix_results_height(result_container) {
  var cont_height = result_container.outerHeight();
  result_container.siblings('.left-col').css({ height: cont_height });
}

/* toggle next tr element
 */
function reveal(element, selector) {
  var link_jq = $(element);
  var tr = link_jq.closest('tr');
  var next = tr.next(selector);
  next.toggle();
}

function reveal_sibling(element, selector) {
  var link_jq = $(element);
  var next = link_jq.siblings(selector);
  next.toggle();
}

function grandchildren(jq_element, selectors) {
  var res_elems = jq_element;
  for (var i = 0; i <= selectors.length - 1; i++) {
    res_elems = res_elems.children(selectors[i]);
  };
  return res_elems;
}

function get_parent_element(element, selector) {
  var element_jq = $(element);
  return element_jq.parent(selector);
}

function reveal_groups_children(element, selectors) {
  var children = get_parent_element(element, 'li')
  children = grandchildren(children, selectors);
  children.toggle()
}

function hide_subelements(element, selectors) {
  var children = get_parent_element(element, 'li');
  children = grandchildren(children, selectors);
  children.hide();
}

function get_result_type(e, prefix) {
  var classes = e.classList;
  for (var i = 0; i <= classes.length - 1; i++) {
    if (classes[i].match(new RegExp('^' + prefix))) {
      return classes[i].substring(prefix.length);
    }
  };
}

function set_test_result_max_height() {
  var elem_max_height = $(window).height() * 2 / 3;
  var elem_max_height_str = elem_max_height.toString() + 'px';
  $(".test-result-inner-container").css('max-height', elem_max_height_str);
}

/* open all visible groups
 */
function unfold_groups(result_container) {
  var container = result_container.find('> .container-listing');

  var groups = container.find('ul.entry-list > li');

  // show groups, toggle indicators
  groups.show();
  var icons = groups.find('> div > div > span.icon');
  icons.addClass('opened');
  icons.removeClass('closed');

  // close indicator whether test is opened
  var tests = groups.find('> div.test-row > div > span.icon');
  tests.addClass('closed');
  tests.removeClass('opened');

  // hide test info
  result_container.find('.test-info-row').hide();
}

 /* close -- fold, all visible groups
  */
function fold_groups(result_container) {
  var container = result_container.find('> .container-listing');

  var sub_groups = container.find('ul.root-groups ul.entry-list > li');
  var all_groups = container.find('ul.entry-list > li');

  // show groups, toggle indicators
  sub_groups.hide();
  var icons = all_groups.find('> div > div > span.icon');
  icons.addClass('closed');
  icons.removeClass('opened');

  // close indicator whether test is opened
  var tests = all_groups.find('> div.test-row > div > span.icon');
  tests.addClass('closed');
  tests.removeClass('opened');

  // hide test info
  result_container.find('.test-info-row').hide();
  // hide test result row
  result_container.find('.test-row-container').hide();
}

function unfold_result(result_id) {
  var result_container = $('#result-' + result_id + '-runhosts .result-container');
  unfold_groups(result_container);
}

$('#id_risk').change(function(){
  filterform.submit();
});

$('.group-row').on("change", ".all-states-checkbox", function() {
  var this_jq = $(this);
  var is_checked = this_jq.prop('checked')
  var form = this_jq.parents('.state').siblings('.filter-by-state-form');
  var inputs = form.find('input[type="checkbox"]');
  if (!is_checked) {
    inputs.prop('checked', false);
  } else {
    inputs.prop('checked', true);
  }
});

/* AJAX
 */
/*
function append_result(result_tr, data) {
  result_tr.html(data['content']);
}*/

/* load data for specified result
 */
function load_result(result_tr, result_id, url_suffix) {
  // this thing is really tricky:
  //  * if it runs on quick network/machine, this causes unwanted ugly flashes
  //  * without *running* icon on slow network, user may think that app just froze
  result_tr.html('<td colspan="8"><div class="center"><span class="pficon pficon-running fa-spin run-state-icon"></span></div></td>')
  $.get('/' + result_id + '/ajax/?' + url_suffix, {}, function(data){
    if (data['status'] == 'OK') {
      result_tr.html(data['content']);
      if (url_suffix.length > 0) {
        unfold_result(result_id);
      }
      set_test_result_max_height();
    } else {
      result_tr.html('<td colspan="8">' + data['content'] + '</td>');
    }
  }).fail(function() {
    result_tr.html('<td colspan="8">There was an error during request processing.</td>');
  });
}

function get_filter_form() {
  var filt_form= $('#filter-form');
  var filt_form_inputs = $('#filter-form').find(':input').not(':submit');
  var filter_form_has_data = false;
  for (var i = 0; i <= filt_form_inputs.length - 1; i++) {
    if (filt_form_inputs[i].value != '') {
      filter_form_has_data = true;
      break;
    }
  };
  if (filter_form_has_data) {
    return filt_form;
  } else {
    return "";
  }
}

function serialize_filter_form() {
  var filter_form = get_filter_form();
  if (filter_form == "") {
    return ""
  } else {
    return filter_form.serialize();
  }
}

function load_and_expand_result(result_id) {
  load_result($("#result-" + result_id + "-runhosts"), result_id, serialize_filter_form());
}

function get_state_filter_form(form_button) {
  var form_button_jq = $(form_button);

  var filt_form_inputs = $('#filter-form').find(':input').not(':submit');
  var state_filter_form = form_button_jq.parent('form.filter-by-state-form');

  var filter_form_has_data = false;
  for (var i = 0; i <= filt_form_inputs.length - 1; i++) {
    if (filt_form_inputs[i].value != '') {
      filter_form_has_data = true;
      break;
    }
  };
  if (form_button_jq[0].name == "filter-all") {
    state_filter_form.append('<input type="hidden" name="filter" value="all" /> ');
  }
  //state_filter_form.children('input[type="submit"]').remove();
  if (filter_form_has_data) {
    filt_form_inputs.clone().hide().attr('isacopy','y').appendTo(state_filter_form);
  }

  return state_filter_form
}

function state_filter(elem){
  var state_filter_form = get_state_filter_form(elem);
  var result_tr = $(elem).parents('tr.group-row');
  var tr_id = result_tr[0].id.split('-')[1];
  load_result(result_tr, tr_id, state_filter_form.serialize());
}

$('.group-row').on("click", ".filter-by-all", function() {
  state_filter(this);
});

$('.group-row').on("click", '.apply-state-filters-btn', function() {
  state_filter(this);
});

$(window).resize(function(){
  set_test_result_max_height();
});

/* collapse all button
 */
$('.group-row').on("click", ".collapse-all-btn", function() {
  var this_jq = $(this);
  var result_container = this_jq.parents('.result-container');
  fold_groups(result_container);
});

/* expand all button
 */
$('.group-row').on("click", ".expand-all-btn", function() {
  var this_jq = $(this);
  var result_container = this_jq.parents('.result-container');
  unfold_groups(result_container);
});

/* select all runs
 */
$('#hostrun-select-all').change(function() {
  checked = $(this).prop('checked');
  $('.hostrun-select-input').prop('checked', checked);
  if (checked) {
    $('.hostrun-row').addClass('hostrun-row-selected');
  } else {
    $('.hostrun-row').removeClass('hostrun-row-selected');
  }
});

/* select run
 */
$('.hostrun-select-input').change(function() {
  var tr_jq = $(this).parent().parent().parent();
  if (this.checked) {
    tr_jq.addClass('hostrun-row-selected');
  } else {
    tr_jq.removeClass('hostrun-row-selected');
    $('#hostrun-select-all').prop('checked', false);
  }
});

/* reveal runs
 */
$('.hostrun-toggle').click(function() {
  var tr_jq = $(this).parent();
  var icon = tr_jq.find('> td > span.icon');
  icon.toggleClass('opened');
  icon.toggleClass('closed');
  var tr_id = tr_jq[0].id.split('-')[3];
  var result_tr = $('#result-' + tr_id + '-runhosts');
  if (result_tr.children().length <= 0) {
    load_result(result_tr, tr_id, serialize_filter_form());
  } else {
    reveal_sibling(this.parentNode, '#result-' + tr_id + '-runhosts');
  }
});

/* reveal tests and child groups
 */
$('.group-row').on("click", ".group-item-row", function() {
  var this_jq = $(this);
  if (this_jq.hasClass('link')) {
    var icon = this_jq.find('> .row-title > span.icon');

    // > v sign toggle
    icon.toggleClass('opened');
    icon.toggleClass('closed');

    reveal_groups_children(this, ['ul.entry-list', 'li']);
  }
});

/* reveal tests
 */
$('.group-row').on("click", ".test-row", function() {
  var this_jq = $(this);
  var icon = this_jq.find('> div > span.icon');
  icon.toggleClass('opened');
  icon.toggleClass('closed');
  reveal_sibling(this, '.test-info-row');

  //fix height of left column
  fix_results_height(this_jq.next('div.test-info-row').children('div.test-result-container'));
});

/* COMPARE */

$('.compare-left-field, .compare-right-field').change(function(){
  var this_jq=$(this);
  var form=$('form#compare-form');
  var both_filled=true;
  $('select.compare-left-field, select.compare-right-field').each(function() {
    both_filled = both_filled && ($(this).val() != "");
  });
  if (both_filled){
    form.submit();
  }
});

$('table#compare-table tbody tr td div.test-title.link').click(function(){
  var this_jq=$(this);
  this_jq.siblings('div.test-details').toggle();
  this_jq.parent().siblings('td').children('div.test-details').toggle();
});

$('table#compare-table tbody tr td div.test-details button.toggle-solution-btn').click(function(){
  var this_jq=$(this);
  var sol_text_cont=this_jq.parent().siblings('div.solution-text-container');
  if (sol_text_cont.is(":visible")){
    this_jq.html("Show additional information");
  } else {
    this_jq.html("Hide additional information");
  }
  sol_text_cont.toggle();
});

