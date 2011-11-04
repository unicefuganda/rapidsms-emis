'''
Created on Sep 15, 2011

@author: asseym
'''
from script.utils.handling import find_best_response
from script.models import Script, ScriptSession, ScriptProgress
from .models import EmisReporter, _schedule_monthly_script
from rapidsms.models import Connection
from datetime import datetime,date

import xlwt
from contact.models import MessageFlag
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from poll.models import Poll
from script.models import ScriptStep
from django.db.models import Count
from django.conf import settings
from uganda_common.utils import *
from education.reports import *



def match_connections():
    script = Script.objects.get(slug='emis_autoreg')
    name_poll = script.steps.get(order=6).poll
    for connection in Connection.objects.all():
        try:
            session = ScriptSession.objects.filter(script=script, connection=connection).order_by('-end_time')[0]
        except IndexError:
            print 'Session for ' + connection.identity + ' does not exist!'
            continue
        try:
            name = find_best_response(session, name_poll)
        except AttributeError:
            import pdb;pdb.set_trace()
            find_best_response(session, name_poll)
        if name:
            name = ' '.join([n.capitalize() for n in name.lower().split(' ')])
            try:
                contact = EmisReporter.objects.get(name=name[:100])
                connection.contact = contact
                connection.save()
            except EmisReporter.MultipleObjectsReturned:
                print name[:100] + ' registered more than once!'
            except EmisReporter.DoesNotExist:
                print name[:100] + ' with connection ' + connection.identity + ' does not exist'

    #    connections = Connection.objects.filter(identity__in=['256774611460','256772544169','256772858848','256700601485','256777092848','256772966162','256782505870','256778301798'])
    #    for connection in connections:
    #        connection.contact = None
    #        connection.save()


def get_contacts(**kwargs):
    request = kwargs.pop('request')
    if request.user.is_authenticated() and hasattr(Contact, 'groups'):
        return Contact.objects.filter(groups__in=request.user.groups.all()).distinct().annotate(Count('responses'))
    else:
        return Contact.objects.annotate(Count('responses'))

def get_polls(**kwargs):
    script_polls = ScriptStep.objects.exclude(poll=None).values_list('poll', flat=True)
    return Poll.objects.exclude(pk__in=script_polls).annotate(Count('responses'))

def get_script_polls(**kwargs):
    script_polls = ScriptStep.objects.exclude(poll=None).values_list('poll', flat=True)
    return Poll.objects.filter(pk__in=script_polls).annotate(Count('responses'))

#def retrieve_poll(request):
#    pks=request.GET.get('pks', '').split('+')
#    if pks[0] == 'l':
#        return [Poll.objects.latest('start_date')]
#    else:
#        pks=[eval(x) for x in list(str(pks[0]).rsplit())]
#        return Poll.objects.filter(pk__in=pks)

def retrieve_poll(request, pks=None):
    script_polls = ScriptStep.objects.exclude(poll=None).values_list('poll', flat=True)
    if pks == None:
        pks = request.GET.get('pks', '')
    if pks == 'l':
        return [Poll.objects.exclude(pk__in=script_polls).latest('start_date')]
    else:
        return Poll.objects.filter(pk__in=[pks]).exclude(pk__in=script_polls)

def get_flagged_messages(**kwargs):

    return MessageFlag.objects.all()

# a manual reschedule of all monthly polls
def reschedule_monthly_polls():
    slugs = ['emis_abuse', 'emis_meals', 'emis_school_administrative', 'emis_smc_monthly']
    #enable scripts in case they are disabled
    Script.objects.filter(slug__in=slugs).update(enabled=True)
    #first remove all existing script progress for the monthly scripts
    ScriptProgress.objects.filter(script__slug__in=slugs).delete()
    for slug in slugs:
        reporters = EmisReporter.objects.all()
        for reporter in reporters:
            if reporter.default_connection and reporter.groups.count() > 0:
                connection = reporter.default_connection
                group = reporter.groups.all()[0]
                if slug == 'emis_abuse':
                    _schedule_monthly_script(group, connection, 'emis_abuse', 'last', ['Teachers', 'Head Teachers'])
                elif slug == 'emis_meals':
                    _schedule_monthly_script(group, connection, 'emis_meals', 20, ['Teachers', 'Head Teachers'])
                elif slug == 'emis_school_administrative':
                    _schedule_monthly_script(group, connection, 'emis_school_administrative', 15, ['Teachers', 'Head Teachers'])
                else:
                    _schedule_monthly_script(group, connection, 'emis_smc_monthly', 28, ['SMC'])

#reschedule weekly SMS questions                
def reschedule_weekly_smc_polls():
    #enable script in case its disabled
    Script.objects.filter(slug='emis_head_teacher_presence').update(enabled=True)
    #first destroy all existing script progress for the SMCs
    ScriptProgress.objects.filter(connection__contact__groups__name='SMC', script__slug='emis_head_teacher_presence').delete()
    smcs = EmisReporter.objects.filter(groups__name='SMC')
    import datetime
    for smc in smcs:
        connection = smc.default_connection
        holidays = getattr(settings, 'SCHOOL_HOLIDAYS', [])
        d = datetime.datetime.now()
        # get the date to a thursday
        d = d + datetime.timedelta((3 - d.weekday()) % 7)
        in_holiday = True
        while in_holiday:
            in_holiday = False
            for start, end in holidays:
                if d >= start and d <= end:
                    in_holiday = True
                    break
            if in_holiday:
                d = d + datetime.timedelta(7)
        sp, created = ScriptProgress.objects.get_or_create(connection=connection, script=Script.objects.get(slug='emis_head_teacher_presence'))

        sp.set_time(d)
def produce_data(slug):
    """
    function to produce data once an XForm slug is provided
    function is a WIP; tested for better optimization on DB
    currently to be used to get values based on grades; [p7, p6, p5,..., p1]
    """
    school_xform_data = []
    for school in School.objects.all():
        try:
            #xforms of all submitted data about schools
            school_xform_data.append(XFormSubmissionValue.objects.exclude(submission__has_errors=True).filter(attribute__slug__in=slug,submission__connection__contact__emisreporter__schools=school).order_by('-created'))
        except IndexError:
            school_xform_data.append(0)

    #processing this data; for large memory, should still be fast
    school_names = [school.name for school in School.objects.all()]

    new_list_buffer = []

    for school_data in school_xform_data:
        new_list_buffer.append(school_data[:7]) #sliced to accomodate the first 7 values corresponding to dates and more recent
    data = []

    def compute_value(list):
        #function to compute value quickly
        if not list:
            return [0,0,0,0,0,0,0]
        else: #for lists with items belonging to the XFormSubmissionValue class
            x = [i.value_int for i in list]
            x.reverse()
            return x

    for school,lis in zip(school_names,new_list_buffer):
        cache = compute_value(lis)
        cache.insert(0,school)
        data.append(cache)
    return data

def create_excel_dataset():
    """
    # for excelification
    for up to 6 districts
    a function to return some excel output from varying datasets
    """
    #This can be expanded for other districts using the rapidSMS locations models
    #CURRENT_DISTRICTS = Location.objects.filter(name__in=XFormSubmissionValue.objects.values_list('submission__connection__contact__reporting_location__name', flat=True)).order_by('name')

    #location = Location.tree.root_nodes()[0]
    start_date, end_date = previous_calendar_week()
    dates = {'start':start_date, 'end':end_date}
    # initialize Excel workbook and set encoding
    book = xlwt.Workbook(encoding='utf8')

    def write_xls(sheet_name, headings, data):
        sheet = book.add_sheet(sheet_name)
        rowx = 0
        for colx, value in enumerate(headings):
            sheet.write(rowx, colx, value)
        sheet.set_panes_frozen(True) # frozen headings instead of split panes
        sheet.set_horz_split_pos(rowx+1) # in general, freeze after last heading row
        sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
        for row in data:
            rowx += 1
            for colx, value in enumerate(row):
                sheet.write(rowx, colx, value)
            
    GRADES = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']
    boy_attendance_slugs = ['boys_%s'% g for g in GRADES]
    girl_attendance_slugs = ['girls_%s'%g for g in GRADES]
    boy_enrolled_slugs = ["enrolledb_%s"%g for g in GRADES]
    girl_enrolled_slugs = ["enrolledg_%s"%g for g in GRADES]

    #Boys attendance
    headings = ["School"] + GRADES
    data_set = produce_data(boy_attendance_slugs)
    write_xls("Latest Attendance for Boys",headings,data_set)

    #Girls attendance
    headings = ["School"] + GRADES
    data_set = produce_data(girl_attendance_slugs)
    write_xls("Latest Attendance for Girls",headings,data_set)

    #Boys enrollment
    headings = ["School"] + GRADES
    data_set = produce_data(boy_enrolled_slugs)
    write_xls("Latest Enrollment for Boys",headings,data_set)

    #Girls Enorllment
    headings = ["School"] + GRADES
    data_set = produce_data(girl_enrolled_slugs)
    write_xls("Latest Enrollment for Girls",headings,data_set)

    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=emis.xls'
    book.save(response)
    return response