from django.db.models import Count
from generic.reports import Column, Report
from rapidsms.contrib.locations.models import Location
from uganda_common.reports import XFormSubmissionColumn, XFormAttributeColumn, PollNumericResultsColumn, PollCategoryResultsColumn, LocationReport
from uganda_common.utils import total_submissions, reorganize_location, total_attribute_value, get_location_for_user, previous_calendar_week, previous_calendar_month
import datetime

GRADES = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']

class AverageSubmissionBySchoolColumn(Column):
    def __init__(self, keyword, extra_filters=None):
        self.keyword = keyword
        self.extra_filters = extra_filters

    def add_to_report(self, report, key, dictionary):
        val = total_submissions(self.keyword, report.start_date, report.end_date, report.location, self.extra_filters)
        for rdict in val:
            rdict['value'] = rdict['value'] / Location.objects.get(pk=rdict['location_id']).get_descendants(include_self=True).aggregate(Count('schools'))['schools__count']
        reorganize_location(key, val, dictionary)


class AverageAttributeBySchoolColumn(Column):
    def __init__(self, keyword, extra_filters=None):
        self.keyword = keyword
        self.extra_filters = extra_filters

    def add_to_report(self, report, key, dictionary):
        val = total_attribute_value(self.keyword, report.start_date, report.end_date, report.location, self.extra_filters)
        for rdict in val:
            rdict['value'] = rdict['value'] / Location.objects.get(pk=rdict['location_id']).get_descendants(include_self=True).aggregate(Count('schools'))['schools__count']
        reorganize_location(key, val, dictionary)


class MainEmisReport(LocationReport):
    boys_p3 = XFormAttributeColumn('boys_p3')
    girls_p3 = XFormAttributeColumn('girls_p3')

    boys_p5 = XFormAttributeColumn('boys_p5')
    girls_p5 = XFormAttributeColumn('girls_p5')

    deploy_m = XFormAttributeColumn('deploy_m')
    deploy_f = XFormAttributeColumn('deploy_f')

    gemabuse_cases = XFormAttributeColumn('gemabuse_cases')
    classrooms_p4 = XFormAttributeColumn('classrooms_p5')

class ClassRoomReport(LocationReport):
    classrooms_p1 = XFormAttributeColumn('classrooms_p1')
    classroomsused_p1 = XFormAttributeColumn('classroomsused_p1')

    classrooms_p2 = XFormAttributeColumn('classrooms_p2')
    classroomsused_p2 = XFormAttributeColumn('classroomsused_p2')

    classrooms_p3 = XFormAttributeColumn('classrooms_p3')
    classroomsused_p3 = XFormAttributeColumn('classroomsused_p3')

    classrooms_p4 = XFormAttributeColumn('classrooms_p4')
    classroomsused_p4 = XFormAttributeColumn('classroomsused_p4')

    classrooms_p5 = XFormAttributeColumn('classrooms_p5')
    classroomsused_p5 = XFormAttributeColumn('classroomsused_p5')

    classrooms_p6 = XFormAttributeColumn('classrooms_p6')
    classroomsused_p6 = XFormAttributeColumn('classroomsused_p6')

    classrooms_p7 = XFormAttributeColumn('classrooms_p7')
    classroomsused_p7 = XFormAttributeColumn('classroomsused_p7')

class DashBoardReport(LocationReport):
    pupil_attendance = XFormAttributeColumn((["boys_%s" % g for g in GRADES] + ["girls_%s" % g for g in GRADES]))
    teacher_attendance = XFormAttributeColumn("gemteachers_htpresent")
    total_enrollment = XFormAttributeColumn((["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]))
    teacher_deployment = XFormAttributeColumn(["deploy_m", "deploy_g"])
    abuse = XFormAttributeColumn("gemabuse_cases")


class AttendanceReport(LocationReport):
    boys = XFormAttributeColumn(["boys_%s" % g for g in GRADES])
    girls = XFormAttributeColumn(["girls_%s" % g for g in GRADES])
    total_pupils = XFormAttributeColumn((["boys_%s" % g for g in GRADES] + ["girls_%s" % g for g in GRADES]))
    male_teachers = XFormAttributeColumn("teachers_f")
    female_teachers = XFormAttributeColumn("teachers_m")
    total_teachers = XFormAttributeColumn(["teachers_m", "teachers_f"])

class HtAttendanceReport(LocationReport):
    htattendance = XFormAttributeColumn("gemteachers_htpresent")
#    htdeployment = TotalSchools()
#    htpercentage = HtPercentage()

class EnrollmentReport(LocationReport):
    boys = XFormAttributeColumn(["enrolledb_%s" % g for g in GRADES])
    girls = XFormAttributeColumn(["enrolledg_%s" % g for g in GRADES])
    total_pupils = XFormAttributeColumn((["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]))
    male_teachers = XFormAttributeColumn("deploy_f")
    female_teachers = XFormAttributeColumn("deploy_m")
    total_teachers = XFormAttributeColumn(["deploy_m", "deploy_f"])

class AbuseReport(LocationReport):
    gem_abuse = XFormAttributeColumn("gemabuse_cases")
#    ht_abuse = XFormAttributeColumn("htabuse_cases")

def location_values(location, data_dicts):
    for dict in data_dicts:
        if dict['location_name'] == location.name:
            if dict['value']:
                return dict['value']
            else:
                return '-'

def attendance_stats(request):
    stats = []
    user_location = get_location_for_user(request.user)
    if not user_location:
        user_location = Location.objects.get(name='Kaabong')
    location = Location.tree.root_nodes()[0]
    start_date, end_date = previous_calendar_week()
    dates = {'start':start_date, 'end':end_date}
    boys = ["boys_%s" % g for g in GRADES]
    values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
    stats.append(('boys', location_values(user_location, values)))

    girls = ["girls_%s" % g for g in GRADES]
    values = total_attribute_value(girls, start_date=start_date, end_date=end_date, location=location)
    stats.append(('girls', location_values(user_location, values)))

    total_pupils = ["boys_%s" % g for g in GRADES] + ["girls_%s" % g for g in GRADES]
    values = total_attribute_value(total_pupils, start_date=start_date, end_date=end_date, location=location)
    stats.append(('total pupils', location_values(user_location, values)))

    values = total_attribute_value("teachers_f", start_date=start_date, end_date=end_date, location=location)
    stats.append(('female teachers', location_values(user_location, values)))

    values = total_attribute_value("teachers_m", start_date=start_date, end_date=end_date, location=location)
    stats.append(('male teachers', location_values(user_location, values)))

    values = total_attribute_value(["teachers_f", "teachers_m"], start_date=start_date, end_date=end_date, location=location)
    stats.append(('total teachers', location_values(user_location, values)))
    res = {}
    res['dates'] = dates
    res['stats'] = stats
    return res

def enrollment_stats(request):
    stats = []
    user_location = get_location_for_user(request.user)
    if not user_location:
        user_location = Location.objects.get(name='Kaabong')
    location = Location.tree.root_nodes()[0]
#    start_date, end_date = previous_calendar_week()
    start_date = datetime.datetime(datetime.datetime.now().year, 1, 1)
    end_date = datetime.datetime.now()
    dates = {'start':start_date, 'end':end_date}
    boys = ["enrolledb_%s" % g for g in GRADES]
    values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
    stats.append(('boys', location_values(user_location, values)))

    girls = ["enrolledg_%s" % g for g in GRADES]
    values = total_attribute_value(girls, start_date=start_date, end_date=end_date, location=location)
    stats.append(('girls', location_values(user_location, values)))

    total_pupils = ["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]
    values = total_attribute_value(total_pupils, start_date=start_date, end_date=end_date, location=location)
    stats.append(('total pupils', location_values(user_location, values)))

    values = total_attribute_value("deploy_f", start_date=start_date, end_date=end_date, location=location)
    stats.append(('female teachers', location_values(user_location, values)))

    values = total_attribute_value("deploy_m", start_date=start_date, end_date=end_date, location=location)
    stats.append(('male teachers', location_values(user_location, values)))

    values = total_attribute_value(["deploy_f", "deploy_m"], start_date=start_date, end_date=end_date, location=location)
    stats.append(('total teachers', location_values(user_location, values)))

    res = {}
    res['dates'] = dates
    res['stats'] = stats
    return res

def headteacher_attendance_stats(request):
    stats = []
    user_location = get_location_for_user(request.user)
    if not user_location:
        user_location = Location.objects.get(name='Kaabong')
    location = Location.tree.root_nodes()[0]
    start_date, end_date = previous_calendar_month()
    dates = {'start':start_date, 'end':end_date}
    values = total_submissions("gemteachers_htpresent", start_date=start_date, end_date=end_date, location=location, extra_filters={'eav__gemteachers_htpresent':1})
    stats.append(('head teacher attendance', location_values(user_location, values)))
    stats.append(('total head teacher deployment', Location.objects.get(pk=user_location.pk).get_descendants(include_self=True).aggregate(Count('schools'))['schools__count']))
    perc = values.count() / Location.objects.get(pk=user_location.pk).get_descendants(include_self=True).aggregate(Count('schools'))['schools__count'] * 100
    stats.append(('percentage attendance', perc))
    res = {}
    res['dates'] = dates
    res['stats'] = stats
    return res
