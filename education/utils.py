from django.contrib.auth.models import User
XFORMS = ()
XFORM_FIELDS = {}

def init_structures(sender, **kwargs):
    pass

def init_xforms(sender, **kwargs):
    pass

def init_autoreg(sender, **kwargs):
    pass

def init_scripts(sender, **kwargs):
    pass

def init_xforms():
    init_xforms_from_tuples(XFORMS, XFORM_FIELDS)

def init_xforms_from_tuples(xforms, xform_fields):
    user = User.objects.get(username='admin')
    xform_dict = {}
    for keyword_prefix,keyword,separator,name,description in xforms:
        xform, created = XForm.objects.get_or_create(
            keyword=keyword,
            keyword_prefix=keyword_prefix,
            defaults={
                'name':name,
                'description':description,
                'response':'',
                'active':True,
                'owner':user,
                'site':Site.objects.get_current(),
                'separator':separator,
                'command_prefix':'',
            }
        )
        xform_dict["%s%s" % (keyword_prefix, keyword)] = xform

    for form_key, attributes in xform_fields.items():
        order = 0
        form = xform_dict[form_key]
        for command, field_type, description, required in attributes:
            xformfield, created = XFormField.objects.get_or_create(
                command=command,
                xform=form,
                defaults={
                    'order':order,
                    'field_type':field_type,
                    'type':field_type,
                    'name':description,
                    'description':description,
                }
            )
            if required:
                xformfieldconstraint, created = XFormFieldConstraint.objects.get_or_create(
                    field=xformfield,
                    defaults={
                        'type':'req_val',
                         'message':("Expected %s, none provided." % description)
                    }
            )
            order = order + 1
    return xform_dict