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
from django.db.models import Avg

def previous_calendar_week(t=None):
    """
    To education monitoring, a week runs between Wednesdays, 
    Thursday marks the beginning of a new week of data submission
    New data for a new week is accepted until Wednesday evenning of the following week
    """
    d = datetime.datetime.now()
    if not d.weekday() == 2:
        # last wednesday == next wednesday minus 7 days.
        last_wednesday = d + (datetime.timedelta((2-d.weekday())%7) - (datetime.timedelta(days=7)))
    else:
        last_wednesday = d
    end_date = last_wednesday + datetime.timedelta(days=7)
    return (last_wednesday, end_date)

def compute_total(chunkit):
    # function takes in a list of tuples (school_name,value) ---> all grades p1 to p7
    new_dict = {}
    for n, val in chunkit: new_dict[n] = 0 #placeholder
    for i in chunkit:
        if i[0] in new_dict.keys():
            new_dict[i[0]] = new_dict[i[0]] + i[1]            
    return new_dict

def previous_calendar_week_v2(date_now):
    if not date_now.weekday() == 2:
        last_wednesday = date_now + (datetime.timedelta((2-date_now.weekday())%7) - (datetime.timedelta(days=7)))
    else:
        last_wednesday = date_now
    end_date = last_wednesday + datetime.timedelta(days=7)
    return (last_wednesday, end_date)

def previous_calendar_month_week_chunks():
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(29)
    month_in_fours = []
    for i in range(4):
        start_date = start_date + datetime.timedelta(7)
        if start_date < end_date:
            month_in_fours.append(list(previous_calendar_week_v2(start_date))) #might have to miss out on the thursdays???
    return month_in_fours

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
        

def produce_data(request, district_id, dates, slugs,choice=list):
    """
    function to produce data once an XForm slug is provided
    function is a WIP; tested for better optimization on DB
    currently to be used to get values based on grades; [p7, p6, p5,..., p1]
    """
    from .reports import get_location
    user_location = get_location(request, district_id)
    schools = School.objects.filter(location__in=user_location.get_descendants(include_self=True).all())
    values = XFormSubmissionValue.objects.exclude(submission__has_errors=True)\
                .filter(created__range=(dates.get('start'), dates.get('end')))\
                .filter(attribute__slug__in=slugs)\
                .filter(submission__connection__contact__emisreporter__schools__in=schools)\
                .values('submission__connection__contact__emisreporter__schools__name')\
                .values_list('submission__connection__contact__emisreporter__schools__name','value_int')
                #.annotate(Avg('value_int'))

    data = []
    i = 0
    while i < len(values):
        school_values = []
        school_values.append(values[i][0])
        school_values.append(values[i][1])
        for x in range(i,(i+6)):
            try:
                school_values.append(values[x][1])
            except IndexError:
                school_values.append(0)
        i += 6
        data.append(school_values)
    return data

def produce_curated_data():
    #chart data
    pass

def create_excel_dataset(request, district_id):
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
    start_date, end_date = previous_calendar_week()
    dates = {'start':start_date, 'end':end_date}
    data_set = produce_data(request, district_id, dates, boy_attendance_slugs)
    write_xls("Latest Attendance for Boys",headings,data_set)

    #Girls attendance
    headings = ["School"] + GRADES
    data_set = produce_data(request, district_id, dates,  girl_attendance_slugs)
    write_xls("Latest Attendance for Girls",headings,data_set)

    #Boys enrollment
    headings = ["School"] + GRADES
    dates = {'start':datetime.datetime(datetime.datetime.now().year, 1, 1), 'end':datetime.datetime.now()}
    data_set = produce_data(request, district_id, dates, boy_enrolled_slugs)
    write_xls("Latest Enrollment for Boys",headings,data_set)

    #Girls Enorllment
    headings = ["School"] + GRADES
    data_set = produce_data(request, district_id, dates,  girl_enrolled_slugs)
    write_xls("Latest Enrollment for Girls",headings,data_set)

    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=emis.xls'
    book.save(response)
    return response