from django.db.signals import post_syncdb
from django.db import models
from rapidsms.models import Contact
from script.signals import script_progress_was_completed, script_progress
from rapidsms_xforms.models import dl_distance
from uganda_common.utils import find_best_response, find_closest_match
from .utils import *
import re
import calendar

class EmisReporter(models.Model):
    contact = models.ForeignKey(Contact)
    school = models.ForeignKey(School)

class School(models.Model):
    name = models.CharField(max_length=60)
    emis_id = models.CharField(max_length=10)
    location = models.ForeignKey(Location)

    def __unicode__(self):
        return '%s' % self.name

def parse_date(command, value):
    return parse_date_value(value)

def parse_date_value(value):
    try:
        date_expr = re.compile(r"\d{1,2} (?:%s) \d{2,4}" % '|'.join(calendar.month_abbr[1:]))
        date_expr1 = re.compile(r"\d{1,2}-\d{1,2}-\d{2,4}")
        date_expr2 = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}")
        date_expr3 = re.compile(r"\d{1,2}\.\d{1,2}\.\d{2,4}")
        date_expr4 = re.compile(r"\d{2,4}\.\d{1,2}\.\d{1,2}")
        date_expr5 = re.compile(r"\d{2,4}-\d{1,2}-\d{1,2}")

        if date_expr.match(value):
            dt_obj = datetime.strptime(date_str, "%d %b %Y")
        elif date_expr1.match(value):
            dt_obj = datetime.strptime(value, "%d-%m-%Y")
        elif date_expr2.match(value):
            dt_obj = datetime.strptime(value, "%d/%m/%Y")
        elif date_expr3.match(value):
            dt_obj = datetime.strptime(value, "%d.%m.%Y")
        elif date_expr4.match(value):
            dt_obj = datetime.strptime(value, "%Y.%m.%d")
        else:
            dt_obj = datetime.strptime(value, "%Y-%m-%d")

    except ValueError:
        raise ValidationError("Expected date format "
                "(\"dd mmm YYYY\", \"dd/mm/yyyy\", \"dd-mm-yyyy\", \"dd.mm.yyyy\", \"yyyy.mm.dd\" or \"yyyy-mm-dd\"), "
                "but instead received: %s." % value)

    time_tuple = dt_obj.timetuple()
    timestamp = time.mktime(time_tuple)
    return int(timestamp)

def parse_yesno(command, value):
    lvalue = value.lower().strip()
    if dl_distance(lvalue, 'yes') <= 1 or lvalue == 'y':
        return 1
    else:
        return 0

def emis_autoreg(**kwargs):

    connection = kwargs['connection']
    progress = kwargs['sender']
    if not progress.script.slug == 'cvs_autoreg':
        return

    session = ScriptSession.objects.filter(script=progress.script, connection=connection).order_by('-end_time')[0]
    script = progress.script
    role_poll = script.steps.get(order=1).poll
    district_poll = script.steps.get(order=2).poll
    subcounty_poll = script.steps.get(order=3).poll
    school_poll = script.steps.get(order=4).poll
    schools_poll = script.steps.get(order=5).poll
    name_poll = script.steps.get(order=6).poll

    if not connection.contact:
            connection.contact = Contact.objects.create()
            connection.save
    contact = connection.contact

    role = find_best_response(session, role_poll)
    default_group = None
    if Group.objects.filter(name='Other EMIS Reporters').count():
        default_group = Group.objects.get(name='Other EMIS Reporters')
    if role:
        group = find_closest_match(role, Group.objects)
        if group:
            contact.groups.add(group)
        elif default_group:
            contact.groups.add(default_group)
    elif default_group:
        contact.groups.add(default_group)

    subcounty = find_best_response(session, subcounty_poll)
    if subcounty:
        contact.reporting_location = subcounty
    else:
        contact.reporting_location = find_best_response(session, district_poll)

    name = find_best_response(session, namepoll)
    if name:
        contact.name = name[:100]

    if not contact.name:
        contact.name = 'Anonymous User'
    contact.save()

    school = find_best_response(session, school_poll)
    if school:
        school_name = ' '.join([t.capitalize() for t in school.lower().split()])
        reporting_school = School.objects.get(name=school_name, \
                                            location__name=find_best_response(session, subounty_poll), \
                                            location__type='sub_county')

    EmisReporter.objects.create(contact=contact, school=reporting_school)

def emis_autoreg_transition(**kwargs):

    connection = kwargs['connection']
    progress = kwargs['sender']
    if not progress.script.slug == 'emis_autoreg':
        return
    script = progress.script
    role_poll = script.steps.get(order=1).poll
    role = find_best_response(session, role_poll)
    if role:
        group = find_closest_match(role, Group.objects)
    skipsteps = {
        'emis_subcounty':['Teachers', 'Head Teachers', 'SMC', 'GEM'],
        'emis_one_school':['Teachers', 'Head Teachers', 'SMC'],
        'emis_many_school':['GEM'],
    }
    skipped = True
    while skipped:
        skipped = False
        for step_name, roles in skipsteps.items():
            if  progress.step.poll and group and \
                progress.step.poll.name == step_name and group.name not in roles:
                skipped = True
                progress.step = progress.script.steps.get(order=progress.step.order + 1)
                progress.save()
                break


Poll.register_poll_type('date', 'Date Response', parse_date_value, db_type=Attribute.TYPE_OBJECT)

XFormField.register_field_type('emisdate', 'Date', parse_date,
                               db_type=XFormField.TYPE_INT, xforms_type='integer')

XFormField.register_field_type('emisboolean', 'YesNo', parse_date,
                               db_type=XFormField.TYPE_INT, xforms_type='integer')

post_syncdb.connect(init_structures, weak=True)
script_progress_was_completed.connect(emis_autoreg, weak=False)
script_progress.connect(emis_autoreg_transition, weak=False)
