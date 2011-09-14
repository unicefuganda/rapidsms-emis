from django.conf import settings
from django.db.models import Count
from generic.reports import Column, Report
from generic.utils import flatten_list
from rapidsms.contrib.locations.models import Location
from rapidsms_xforms.models import XFormSubmissionValue
from uganda_common.reports import XFormSubmissionColumn, XFormAttributeColumn, PollNumericResultsColumn, PollCategoryResultsColumn, LocationReport
from uganda_common.utils import total_submissions, reorganize_location, total_attribute_value, get_location_for_user

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
    """
    This divides the total number of an indicator (such as, boys weekly attendance) by:
    [the number of non-holiday weeks in the date range * the total of another indicator
    (for instance, boys yearly enrollment)].
    
    This gives you the % expected for two indicators, one that is reported on weekly
    and the other which is a fixed total number.
    """
    def __init__(self, keyword, extra_filters=None):
        self.keyword = keyword
        self.extra_filters = extra_filters

    def add_to_report(self, report, key, dictionary):
        val = total_attribute_value(self.keyword, report.start_date, report.end_date, report.location, self.extra_filters)
        for rdict in val:
            rdict['value'] = rdict['value'] / Location.objects.get(pk=rdict['location_id']).get_descendants(include_self=True).aggregate(Count('schools'))['schools__count']
        reorganize_location(key, val, dictionary)


class AverageWeeklyTotalRatioColumn(Column):



    def __init__(self, weekly_attrib, total_attrib):
        self.weekly_attrib = weekly_attrib
        self.total_attrib = total_attrib

    def add_to_report(self, report, key, dictionary):
        top_val = XFormSubmissionValue.objects.exclude(submission__has_errors=True)\
            .exclude(submission__connection__contact=None)\
            .filter(created__range=(report.start_date, report.end_date))\
            .filter(attribute__slug__in=self.weekly_attrib)\
            .values('submission__connection__contact__emisreporter__school__name')\
            .annotate(Sum('value_int'))


        bottom_val = XFormSubmissionValue.objects.exclude(submission__has_errors=True)\
            .exclude(submission__connection__contact=None)\
            .filter(created__range=(report.start_date, report.end_date))\
            .filter(attribute__slug__in=self.total_attrib)\
            .values('submission__connection__contact__emisreporter__school__name')\
            .annotate(Sum('value_int'))

        td = report.start_date - report.end_date
        holidays = getattr(settings, 'SCHOOL_HOLIDAYS', [])
        for start, end in holidays:
            if start > report.start_date and end < report.end_date:
                td -= (end - start)

        #FIXME : line 78 has a bug, both vals need to return school id and bottom_val needs
        # to be looked up properly
        num_weeks = td.days / 7
        val = []
        for rdict in top_val:
            rdict['value'] = (rdict['value'] / (bottom_val * num_weeks))
            val.append(rdict)

        reorganize_location(key, val, dictionary)


class SchoolReport(Report):
    def __init__(self, request, dates):
        try:
            self.location = get_location_for_user(request.user)
        except:
            pass
        if self.location is None:
            self.location = Location.tree.root_nodes()[0]
        Report.__init__(self, request, dates)


class DatelessSchoolReport(Report):
    def __init__(self, request=None, dates=None):
        try:
            self.location = get_location_for_user(request.user)
        except:
            pass
        if self.location is None:
            self.location = Location.tree.root_nodes()[0]

        self.report = {} #SortedDict()
        self.columns = []
        column_classes = Column.__subclasses__()
        for attrname in dir(self):
            val = getattr(self, attrname)
            if type(val) in column_classes:
                self.columns.append(attrname)
                val.add_to_report(self, attrname, self.report)

        self.report = flatten_list(self.report)


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
    htdeployment = TotalSchools()
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

