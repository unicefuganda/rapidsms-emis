from django.contrib.auth.models import User
from rapidsms_xforms.models import Xform, XformField, XformConstraint

XFORMS = (
          ('', 'boys', ',;:*.\\s"', 'Boys Attendance', 'Weekly Attendance for Boys'),
          ('', 'girls', ',;:*.\\s"', 'Girls Attendance', 'Weekly Attendance for Girls'),
          ('', 'teachers', ',;:*.\\s"', 'Teachers Attendance', 'Weekly Attendance for Teachers'),
          ('', 'classrooms', ',;:*.\\s"', 'Classrooms', 'Classrooms at School'),
          ('', 'classroomsused', ',;:*.\\s"', 'Used Classrooms', 'Classrooms in use at School'),
          ('', 'latrines', ',;:*.\\s"', 'Latrines', 'Latrines at School'),
          ('', 'latrinesused', ',;:*.\\s"', 'Used Latrines', 'Latrines in use at School'),
          ('', 'deploy', ',;:*.\\s"', 'Deployment', 'Teacher Deployment'),
          ('', 'enrolledb', ',;:*.\\s"', 'Boys Enrolment', 'Number of Boys enrolled at School'),
          ('', 'enrolledg', ',;:*.\\s"', 'Girls Enrolment', 'Number of Girls enrolled at School'),
          ('', 'gemabuse', ',;:*.\\s"', 'GEM Abuse Cases', 'Number of abuses happening in Schools reported to GEM'),
          ('', 'gemteachers', ',;:*.\\s"', 'GEM Teacher Attendance', 'Number of Head Teacher presence at School based on last Visit'),
          )

XFORM_FIELDS = {
        'boys':[
                ('date', 'emisdate', 'Date of Attendance Record', True),
                ('p1', 'int', 'Number of boys in P1', True),
                ('p2', 'int', 'Number of boys in P2', True),
                ('p3', 'int', 'Number of boys in P3', True),
                ('p4', 'int', 'Number of boys in P4', True),
                ('p5', 'int', 'Number of boys in P5', True),
                ('p6', 'int', 'Number of boys in P6', True),
                ('p7', 'int', 'Number of boys in P7', True),
         ],
        'girls':[
                ('date', 'emisdate', 'Date of Attendance Record', True),
                ('p1', 'int', 'Number of girls in P1', True),
                ('p2', 'int', 'Number of girls in P2', True),
                ('p3', 'int', 'Number of girls in P3', True),
                ('p4', 'int', 'Number of girls in P4', True),
                ('p5', 'int', 'Number of girls in P5', True),
                ('p6', 'int', 'Number of girls in P6', True),
                ('p7', 'int', 'Number of girls in P7', True),
         ],
        'teachers':[
                ('date', 'emisdate', 'Date of Attendance Record', True),
                ('female', 'int', 'Number of girls in P1', True),
                ('male', 'int', 'Number of girls in P2', True),
         ],
        'classrooms':[
                ('p1', 'int', 'Number of girls in P1', True),
                ('p2', 'int', 'Number of girls in P2', True),
                ('p3', 'int', 'Number of girls in P3', True),
                ('p4', 'int', 'Number of girls in P4', True),
                ('p5', 'int', 'Number of girls in P5', True),
                ('p6', 'int', 'Number of girls in P6', True),
                ('p7', 'int', 'Number of girls in P7', True),
         ],
        'classroomsused':[
                ('p1', 'int', 'Number of girls in P1', True),
                ('p2', 'int', 'Number of girls in P2', True),
                ('p3', 'int', 'Number of girls in P3', True),
                ('p4', 'int', 'Number of girls in P4', True),
                ('p5', 'int', 'Number of girls in P5', True),
                ('p6', 'int', 'Number of girls in P6', True),
                ('p7', 'int', 'Number of girls in P7', True),
         ],
                }

def init_structures(sender, **kwargs):
    pass

def init_xforms(sender, **kwargs):
    init_xforms_from_tuples(XFORMS, XFORM_FIELDS)

def init_autoreg(sender, **kwargs):
    pass

def init_scripts(sender, **kwargs):
    pass

def init_xforms_from_tuples(xforms, xform_fields):
    user = User.objects.get(username='admin')
    xform_dict = {}
    for keyword_prefix, keyword, separator, name, description in xforms:
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
