function deleteSchool(elem, pk, name, url) {
	alert('here');
    if (confirm('Are you sure you want to remove ' + name + '?')) {
        $(elem).parents('tr').remove();
        $.post(url, function(data) {});
    }
}

function editSchool(elem, pk, url) {
    overlay_loading_panel($(elem).parents('tr'));
    $(elem).parents('tr').load(url, '', function () {
        $('#div_panel_loading').hide();    
    });
}

function submitForm(link, action, resultDiv) {
    form = $(link).parents("form");
    form_data = form.serializeArray();
    resultDiv.load(action, form_data);
}

function deleteSchool(elem,link,name) {
    if (confirm('Are you sure you want to remove ' + name + '?')) {
        $(elem).parents('p').remove();
        $.post(link, function(data) {});
    }
}

function newSchool(elem, link) {
	$('#add_school_form').load(link);
    $('#add_school_anchor_row').hide();
}

function addSchools(elem, action) {
    form = $(elem).parents("form");
    form_data = form.serializeArray();
    $('#add_school_form').load(action, form_data);
}

function addSchoolElm(elem){
	rowelem = $(elem).parents('tr')
    rowelem.after('<tr></tr>')
    name_form = $('#name_elms').html()
    location_form = $('#location_elms').html()
    id_form = $('#id_elms').html()
    rowelem.next().html('<td>Name: </td><td>'+name_form+'</td><td>Location: </td><td>'+location_form+'</td><td>School ID: </td><td>'+id_form+'</td>');
}
