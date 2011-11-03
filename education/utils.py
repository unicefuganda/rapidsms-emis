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


def create_excel_dataset():
    """
    # for excelification
    for up to 6 districts
    a function to return some excel output from varying datasets
    """
    #This can be expanded for other districts using the rapidSMS locations models
    #CURRENT_DISTRICTS = Location.objects.filter(name__in=XFormSubmissionValue.objects.values_list('submission__connection__contact__reporting_location__name', flat=True)).order_by('name')
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

    def xform_data_picker(xform_name=None,*args):
        school_vals = {}
        if xform_name:
            #TODO this part is incomplete and should handle other xform value
            for school in School.objects.all():
                pass
        else:
            for school in School.objects.all():
                grade_val = {}
                for g in GRADES:
                    try:
                        grade_val[g] = XFormSubmissionValue.objects.exclude(submission__has_errors=True).filter(attribute__slug__in=["boys_%s"%g],submission__connection__contact__emisreporter__schools=school).order_by('-created')[:1][0].value_int
                    except IndexError:
                        grade_val[g] = 0
                school_vals[school.name]=grade_val

            
    GRADES = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']
    boy_slugs = ['boys_%s'% g for g in GRADES]
    girl_slugs = ['girls_%s'%g for g in GRADES]
    data = {}
    headings = ["School"].extend(GRADES)
    school_vals = {}
    for school in School.objects.all():
        grade_val = {}
        for g in GRADES:
            try:
                grade_val[g] = XFormSubmissionValue.objects.exclude(submission__has_errors=True).filter(attribute__slug__in=["boys_%s"%g],submission__connection__contact__emisreporter__schools=school).order_by('-created')[:1][0].value_int
            except IndexError:
                grade_val[g] = 0
    school_vals[school.name]=grade_val
    data_set = []
    for school_name,d_set in zip(school_vals.keys(),school_vals.values()):
        data_set.append([school_name]+d_set.values())
    write_xls("boys",headings,data_set)
    
    CURRENT_DISTRICTS_UNDER_EMIS =\
    ["Kaabong",
                                    "Kotido",
                                    "Kabarole",
                                    "Kisoro",
                                    "Kyegegwa",
                                    "Mpigi",
                                    "Kabale"
    ]
    location = Location.tree.root_nodes()[0]
    start_date, end_date = previous_calendar_week()
    dates = {'start':start_date, 'end':end_date}
    # initialize Excel workbook and set encoding
    book = xlwt.Workbook(encoding='utf8')

    # localised data by district
    loc_data = []
    # enrollment data
    headings = ["boys","girls","total pupils","female teachers","male teachers","total teachers"]
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []

        boys = ["boys_%s" % g for g in GRADES]
        values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        girls = ["girls_%s" % g for g in GRADES]
        values = total_attribute_value(girls, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        total_pupils = ["boys_%s" % g for g in GRADES] + ["girls_%s" % g for g in GRADES]
        values = total_attribute_value(total_pupils, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        values = total_attribute_value("teachers_f", start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        values = total_attribute_value("teachers_m", start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        values = total_attribute_value(["teachers_f", "teachers_m"], start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))
        loc_data.append(stats)
    write_xls("All Enrollment",headings,loc_data)


    # Boys attendance in schools
    loc_data = []
    # enrollment data
    headings = GRADES
    headings.insert(0,"School")
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []
        for g in GRADES:
            boys_in = ["boys_%s"%g]
            values = total_attribute_value(boys_in,start_date=start_date,end_date=end_date,location=location)
            stats.append(location_values(user_location,values))
#        boys = ["boys_%s" % g for g in GRADES]
#        values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
#        stats.append(location_values(user_location, values))
        loc_data.append(stats)
    write_xls("Boysattendance",headings,loc_data)


    # Girls attendance in schools
    loc_data = []
    # enrollment data
    headings = GRADES
    #headings.insert(0,"School")
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []
        for g in GRADES:
            boys_in = ["girls_%s"%g]
            values = total_attribute_value(boys_in,start_date=start_date,end_date=end_date,location=location)
            stats.append(location_values(user_location,values))
#        boys = ["boys_%s" % g for g in GRADES]
#        values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
#        stats.append(location_values(user_location, values))
        loc_data.append(stats)
    write_xls("Girlsattendance",headings,loc_data)


    # data in loc_data is organized by district, every new list element is a district under EMIS
    # Enrollment and Deployment
    loc_data = []
    headings = ["Boys","Girls","Total Pupils","Female Teachers","Male Teachers","Total Teachers"]
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []

        boys = ["enrolledb_%s" % g for g in GRADES]
        values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        girls = ["enrolledg_%s" % g for g in GRADES]
        values = total_attribute_value(girls, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        total_pupils = ["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]
        values = total_attribute_value(total_pupils, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        values = total_attribute_value("deploy_f", start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        values = total_attribute_value("deploy_m", start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        values = total_attribute_value(["deploy_f", "deploy_m"], start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))
        loc_data.append(stats)
    write_xls("Enrollment and Deployment",headings,loc_data)
    
    #Students enrolled by district (excludes teachers)
    loc_data = []
    headings = [ "Boys", "Girls", "Total Pupils" ]
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []

        boys = ["enrolledb_%s" % g for g in GRADES]
        values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        girls = ["enrolledg_%s" % g for g in GRADES]
        values = total_attribute_value(girls, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        total_pupils = ["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]
        values = total_attribute_value(total_pupils, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))

        loc_data.append(stats)
    write_xls("Student Enrollment",headings,loc_data)

    # number of boys enrolled per district
    loc_data = []
    headings = ["District","Boys"]
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []

        boys = ["boys_%s" % g for g in GRADES]
        values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))
        stats.insert(0,loc)
        loc_data.append(stats)
    write_xls("Boy enrollment",headings,loc_data)

    #number of girls per district
    loc_data = []
    headings = ["District","Girls"]
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []

        girls = ["girls_%s" % g for g in GRADES]
        values = total_attribute_value(girls, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))
        stats.insert(0,loc)
        loc_data.append(stats)
    write_xls("Girl enrollment",headings,loc_data)
    
    #Classrooms by district
    loc_data = []
    heagings = ["District", "Classrooms"]
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []
        classrooms = ["classrooms_%s" % g for g in GRADES]
        values = total_attribute_value(classrooms, start_date=start_date, end_date=end_date, location=location)
        stats.append(location_values(user_location, values))
        stats.insert(0,loc)
        loc_data.append(stats)
    write_xls("Classrooms by district",headings,loc_data)
    

    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=emis.xls'
    book.save(response)
    return response



