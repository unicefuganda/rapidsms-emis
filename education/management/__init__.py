from django.db.models.signals import post_syncdb
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth.models import User, Group
from rapidsms_xforms.models import XFormField, XForm, XFormSubmission, dl_distance, xform_received
from script.models import *

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
#                ('date', 'emisdate', 'Date of Attendance Record', True),
            ('p1', 'int', 'Number of boys in P1', True),
            ('p2', 'int', 'Number of boys in P2', True),
            ('p3', 'int', 'Number of boys in P3', True),
            ('p4', 'int', 'Number of boys in P4', True),
            ('p5', 'int', 'Number of boys in P5', True),
            ('p6', 'int', 'Number of boys in P6', True),
            ('p7', 'int', 'Number of boys in P7', True),
     ],
    'girls':[
#                ('date', 'emisdate', 'Date of Attendance Record', True),
            ('p1', 'int', 'Number of girls in P1', True),
            ('p2', 'int', 'Number of girls in P2', True),
            ('p3', 'int', 'Number of girls in P3', True),
            ('p4', 'int', 'Number of girls in P4', True),
            ('p5', 'int', 'Number of girls in P5', True),
            ('p6', 'int', 'Number of girls in P6', True),
            ('p7', 'int', 'Number of girls in P7', True),
     ],
    'teachers':[
#                ('date', 'emisdate', 'Date of Attendance Record', True),
            ('f', 'int', 'Number of female teachers present', True),
            ('m', 'int', 'Number of male teachers present', True),
     ],
    'classrooms':[
            ('p1', 'int', 'Number of classrooms for P1', True),
            ('p2', 'int', 'Number of classrooms for P2', True),
            ('p3', 'int', 'Number of classrooms for P3', True),
            ('p4', 'int', 'Number of classrooms for P4', True),
            ('p5', 'int', 'Number of classrooms for P5', True),
            ('p6', 'int', 'Number of classrooms for P6', True),
            ('p7', 'int', 'Number of classrooms for P7', True),
     ],
    'classroomsused':[
            ('p1', 'int', 'Number of classrooms in use for P1', True),
            ('p2', 'int', 'Number of classrooms in use for P2', True),
            ('p3', 'int', 'Number of classrooms in use for P3', True),
            ('p4', 'int', 'Number of classrooms in use for P4', True),
            ('p5', 'int', 'Number of classrooms in use for P5', True),
            ('p6', 'int', 'Number of classrooms in use for P6', True),
            ('p7', 'int', 'Number of classrooms in use for P7', True),
     ],
    'latrines':[
            ('g', 'int', 'Number of Latrines for Girls', True),
            ('b', 'int', 'Number of Latrines for Boys', True),
            ('f', 'int', 'Number of Latries for Female Teachers', True),
            ('m', 'int', 'Number of Latries for Female Teachers', True),
     ],
    'latrinesused':[
            ('g', 'int', 'Number of Latrines for Girls', True),
            ('b', 'int', 'Number of Latrines for Boys', True),
            ('f', 'int', 'Number of Latries for Female Teachers', True),
            ('m', 'int', 'Number of Latries for Male Teachers', True),
     ],
    'deploy':[
            ('f', 'int', 'Number of Female Teachers Deployed', True),
            ('m', 'int', 'Number of Male Teachers Deployed', True),
     ],
    'enrolledb':[
            ('p1', 'int', 'Number of boys enrolled in P1', True),
            ('p2', 'int', 'Number of boys enrolled in P2', True),
            ('p3', 'int', 'Number of boys enrolled in P3', True),
            ('p4', 'int', 'Number of boys enrolled in P4', True),
            ('p5', 'int', 'Number of boys enrolled in P5', True),
            ('p6', 'int', 'Number of boys enrolled in P6', True),
            ('p7', 'int', 'Number of boys enrolled in P7', True),
     ],
    'enrolledg':[
            ('p1', 'int', 'Number of girls enrolled in P1', True),
            ('p2', 'int', 'Number of girls enrolled in P2', True),
            ('p3', 'int', 'Number of girls enrolled in P3', True),
            ('p4', 'int', 'Number of girls enrolled in P4', True),
            ('p5', 'int', 'Number of girls enrolled in P5', True),
            ('p6', 'int', 'Number of girls enrolled in P6', True),
            ('p7', 'int', 'Number of girls enrolled in P7', True),
     ],
    'gemabuse':[
            ('cases', 'int', 'Number of Abuse Cases Reported', True),
            ('school', 'text', 'School Code', True),
     ],
    'gemteachers':[
            ('htpresent', 'emisbool', 'Head Teacher presense at School at Last Visit', True),
            ('school', 'text', 'School Code', True),
     ],
}

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
#                ('date', 'emisdate', 'Date of Attendance Record', True),
            ('p1', 'int', 'Number of boys in P1', True),
            ('p2', 'int', 'Number of boys in P2', True),
            ('p3', 'int', 'Number of boys in P3', True),
            ('p4', 'int', 'Number of boys in P4', True),
            ('p5', 'int', 'Number of boys in P5', True),
            ('p6', 'int', 'Number of boys in P6', True),
            ('p7', 'int', 'Number of boys in P7', True),
     ],
    'girls':[
#                ('date', 'emisdate', 'Date of Attendance Record', True),
            ('p1', 'int', 'Number of girls in P1', True),
            ('p2', 'int', 'Number of girls in P2', True),
            ('p3', 'int', 'Number of girls in P3', True),
            ('p4', 'int', 'Number of girls in P4', True),
            ('p5', 'int', 'Number of girls in P5', True),
            ('p6', 'int', 'Number of girls in P6', True),
            ('p7', 'int', 'Number of girls in P7', True),
     ],
    'teachers':[
#                ('date', 'emisdate', 'Date of Attendance Record', True),
            ('f', 'int', 'Number of female teachers present', True),
            ('m', 'int', 'Number of male teachers present', True),
     ],
    'classrooms':[
            ('p1', 'int', 'Number of classrooms for P1', True),
            ('p2', 'int', 'Number of classrooms for P2', True),
            ('p3', 'int', 'Number of classrooms for P3', True),
            ('p4', 'int', 'Number of classrooms for P4', True),
            ('p5', 'int', 'Number of classrooms for P5', True),
            ('p6', 'int', 'Number of classrooms for P6', True),
            ('p7', 'int', 'Number of classrooms for P7', True),
     ],
    'classroomsused':[
            ('p1', 'int', 'Number of classrooms in use for P1', True),
            ('p2', 'int', 'Number of classrooms in use for P2', True),
            ('p3', 'int', 'Number of classrooms in use for P3', True),
            ('p4', 'int', 'Number of classrooms in use for P4', True),
            ('p5', 'int', 'Number of classrooms in use for P5', True),
            ('p6', 'int', 'Number of classrooms in use for P6', True),
            ('p7', 'int', 'Number of classrooms in use for P7', True),
     ],
    'latrines':[
            ('g', 'int', 'Number of Latrines for Girls', True),
            ('b', 'int', 'Number of Latrines for Boys', True),
            ('f', 'int', 'Number of Latries for Female Teachers', True),
            ('m', 'int', 'Number of Latries for Female Teachers', True),
     ],
    'latrinesused':[
            ('g', 'int', 'Number of Latrines for Girls', True),
            ('b', 'int', 'Number of Latrines for Boys', True),
            ('f', 'int', 'Number of Latries for Female Teachers', True),
            ('m', 'int', 'Number of Latries for Male Teachers', True),
     ],
    'deploy':[
            ('f', 'int', 'Number of Female Teachers Deployed', True),
            ('m', 'int', 'Number of Male Teachers Deployed', True),
     ],
    'enrolledb':[
            ('p1', 'int', 'Number of boys enrolled in P1', True),
            ('p2', 'int', 'Number of boys enrolled in P2', True),
            ('p3', 'int', 'Number of boys enrolled in P3', True),
            ('p4', 'int', 'Number of boys enrolled in P4', True),
            ('p5', 'int', 'Number of boys enrolled in P5', True),
            ('p6', 'int', 'Number of boys enrolled in P6', True),
            ('p7', 'int', 'Number of boys enrolled in P7', True),
     ],
    'enrolledg':[
            ('p1', 'int', 'Number of girls enrolled in P1', True),
            ('p2', 'int', 'Number of girls enrolled in P2', True),
            ('p3', 'int', 'Number of girls enrolled in P3', True),
            ('p4', 'int', 'Number of girls enrolled in P4', True),
            ('p5', 'int', 'Number of girls enrolled in P5', True),
            ('p6', 'int', 'Number of girls enrolled in P6', True),
            ('p7', 'int', 'Number of girls enrolled in P7', True),
     ],
    'gemabuse':[
            ('cases', 'int', 'Number of Abuse Cases Reported', True),
            ('school', 'text', 'School Code', True),
     ],
    'gemteachers':[
            ('htpresent', 'emisbool', 'Head Teacher presense at School at Last Visit', True),
            ('school', 'text', 'School Code', True),
     ],
}

models_created = []
structures_initialized = False

def init_structures(sender, **kwargs):
    global models_created
    global structures_initialized
    models_created.append(sender.__name__)
    required_models = ['eav.models', 'rapidsms_xforms.models', 'poll.models', 'script.models', 'django.contrib.auth.models']
    if 'django.contrib.sites' in settings.INSTALLED_APPS:
        required_models.append('django.contrib.sites.models')
    for required in required_models:
        if required not in models_created:
            return
    if not structures_initialized:
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            site_id = getattr(settings, 'SITE_ID', 1)
            Site.objects.get_or_create(pk=site_id, defaults={'domain':'rapidemis.com'})
        init_groups()
        init_xforms(sender)
        init_autoreg(sender)
        init_scripts(sender)
        structures_initialized = True

def init_groups():
    for g in ['Teachers', 'Head Teachers', 'SMC', 'GEM', 'CCT', 'DEO', 'District Officials', 'Other EMIS Reporters']:
        Group.objects.get_or_create(name=g)

def init_xforms(sender, **kwargs):
    init_xforms_from_tuples(XFORMS, XFORM_FIELDS)

def init_xforms_from_tuples(xforms, xform_fields):
    user, created = User.objects.get_or_create(username='admin')
    xform_dict = {}
    for keyword_prefix, keyword, separator, name, description in xforms:
        form, created = XForm.objects.get_or_create(
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
        if created:
            order = 0
            form_key = "%s%s" % (keyword_prefix, keyword)
            attributes = xform_fields[form_key]
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
            xform_dict[form_key] = form
    return xform_dict

def init_autoreg(sender, **kwargs):
    script, created = Script.objects.get_or_create(
            slug="emis_autoreg", defaults={
            'name':"Education monitoring autoregistration script"})
    if created:
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            script.sites.add(Site.objects.get_current())
        user, created = User.objects.get_or_create(username="admin")

        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="Welcome to the SMS based school data collection pilot.The information you provide is valuable to improving the quality of education in Uganda.",
            order=0,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=0,
            giveup_offset=60,
        ))
        role_poll = Poll.objects.create(\
            name='emis_role', \
            user=user, type=Poll.TYPE_TEXT, \
            question='To register,tell us your role? Teacher, Head Teacher, SMC, GEM, CCT, DEO,or District Official.Reply with one of the roles listed.', \
            default_response=''
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=role_poll,
            order=1,
            rule=ScriptStep.RESEND_MOVEON,
            num_tries=1,
            start_offset=0,
            retry_offset=86400,
            giveup_offset=86400,
        ))
        district_poll = Poll.objects.create(
            user=user, \
            type='district', \
            name='emis_district',
            question='What is the name of your district?', \
            default_response='', \
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=district_poll,
            order=2,
            rule=ScriptStep.STRICT_MOVEON,
            start_offset=0,
            retry_offset=86400,
            num_tries=1,
            giveup_offset=86400,
        ))
        county_poll = Poll.objects.create(
            user=user, \
            type=Poll.TYPE_TEXT, \
            name='emis_subcounty',
            question='What is the name of your sub county?', \
            default_response='', \
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=county_poll,
            order=3,
            rule=ScriptStep.RESEND_MOVEON,
            start_offset=0,
            retry_offset=86400,
            num_tries=1,
            giveup_offset=86400,
        ))
        school1_poll = Poll.objects.create(
            user=user, \
            type=Poll.TYPE_TEXT, \
            name='emis_one_school',
            question='What is the name of your school?', \
            default_response='', \
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=school1_poll,
            order=4,
            rule=ScriptStep.RESEND_MOVEON,
            start_offset=0,
            retry_offset=86400,
            num_tries=1,
            giveup_offset=86400,
        ))
        schoolmany_poll = Poll.objects.create(
            user=user, \
            type=Poll.TYPE_TEXT, \
            name='emis_many_school',
            question='Name the schools you are resonsible for.Separate each school name with a comma, for example "St. Mary Secondary,Pader Primary"', \
            default_response='', \
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=schoolmany_poll,
            order=5,
            rule=ScriptStep.RESEND_MOVEON,
            start_offset=0,
            retry_offset=86400,
            num_tries=1,
            giveup_offset=86400,
        ))
        name_poll = Poll.objects.create(
            user=user, \
            type=Poll.TYPE_TEXT, \
            name='emis_name',
            question='What is your name?', \
            default_response='', \
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=name_poll,
            order=6,
            rule=ScriptStep.RESEND_MOVEON,
            num_tries=1,
            start_offset=60,
            retry_offset=86400,
            giveup_offset=86400,
        ))
        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="Welcome to the school monitoring pilot.The information you provide contributes to keeping children in school.",
            order=7,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=60,
            giveup_offset=0,
        ))
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            for poll in [role_poll, district_poll, county_poll, school1_poll, schoolmany_poll, name_poll]:
                poll.sites.add(Site.objects.get_current())

def init_scripts(sender, **kwargs):
    simple_scripts = {
        'abuse':[(Poll.TYPE_NUMERIC, 'emis_abuse', 'How many abuse cases were recorded in the record book this month?')],
        'meals':[(Poll.TYPE_TEXT, 'emis_meals', 'How many children had meals at lunch today? Reply with ONE of the following - very few, less than half, more than half, very many')],
        'school administrative':[(Poll.TYPE_NUMERIC, 'emis_grant', 'How much of your annual capitation grant have you received this term? Reply with ONE of the following 25%, 50%, 75%% or 100%',),
                                 ('date', 'emis_inspection', 'What date was your last school inspection?',),
                                 ('date', 'emis_cct', 'What date was your last CCT visit?',),
                                ],
        'head teacher presence':[(Poll.TYPE_TEXT, 'emis_absence', 'Do you know if the head teacher was present at school today? Answer YES or NO', True), ],
        'smc monthly':[(Poll.TYPE_TEXT, 'emis_smc_meals', 'How many children did you observe having a meal at lunch today, Reply with ONE of the following- very few, less than half, more than half, very many'),
                              (Poll.TYPE_TEXT, 'emis_grant_notice', 'Has UPE capitation grant been display on school notice board? Answer YES or NO', True), \
                              (Poll.TYPE_TEXT, 'emis_inspection_yesno', 'Do you know if your school was inspected this term? Answer YES if there was inspection and NO if there was no inspection', True),
                              (Poll.TYPE_NUMERIC, 'emis_meetings', 'How many SMC meetings have you held this term?Give number of meetings held, if none, reply 0.'), ],
        'annual':[(Poll.TYPE_TEXT, 'emis_classroom', 'How many classrooms does your school have for each class?'),
                  (Poll.TYPE_TEXT, 'emis_classroom_use', 'How many classrooms are in usen at your school for each class?'),
                  (Poll.TYPE_TEXT, 'emis_latrines', 'How many latrine stances does your school have for boys, girls and teachers?'),
                  (Poll.TYPE_TEXT, 'emis_latrines_use', 'How many latrine stances are used by boys, girls and teachers?'),
                  (Poll.TYPE_TEXT, 'emis_teachers', 'How many male and female teachers are deployed at your school?'),
                  (Poll.TYPE_TEXT, 'emis_boys_enrolled', 'How many boys are enrolled in classes p1-p7 at your school?'),
                  (Poll.TYPE_TEXT, 'emis_girls_enrolled', 'How many girls are enrolled in classes p1-p7 at your school?'), ]
    }

    user, created = User.objects.get_or_create(username='admin')
    for script_name, polls in simple_scripts.items():
        script, created = Script.objects.get_or_create(
            slug="emis_%s" % script_name.lower().replace(' ', '_'), defaults={
            'name':"Education monitoring %s script" % script_name})
        if created:
            script.sites.add(Site.objects.get_current())
            step = 0
            for poll_info in polls:
                poll = Poll.objects.create(
                    user=user, \
                    type=poll_info[0], \
                    name=poll_info[1],
                    question=poll_info[2], \
                    default_response='', \
                )
                poll.sites.add(Site.objects.get_current())

                if len(poll_info) > 3 and poll_info[3]:
                    poll.add_yesno_categories()
                script.steps.add(ScriptStep.objects.create(
                    script=script,
                    poll=poll,
                    order=step,
                    rule=ScriptStep.RESEND_MOVEON,
                    num_tries=1,
                    start_offset=60,
                    retry_offset=86400,
                    giveup_offset=86400,
                ))
                step = step + 1

post_syncdb.connect(init_structures, weak=False)
