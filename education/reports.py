from django.conf import settings
from django.db.models import Count, Sum
from generic.reports import Column, Report
from generic.utils import flatten_list
from rapidsms.contrib.locations.models import Location
from rapidsms_xforms.models import XFormSubmissionValue
from uganda_common.reports import XFormSubmissionColumn, XFormAttributeColumn, PollNumericResultsColumn, PollCategoryResultsColumn, LocationReport
from uganda_common.utils import total_submissions, reorganize_location, total_attribute_value, previous_calendar_week, previous_calendar_month
from uganda_common.utils import reorganize_dictionary
import datetime

GRADES = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']

def get_location_for_user(user):
    return user.get_profile().location

class SchoolMixin(object):
    SCHOOL_ID = 'submission__connection__contact__emisreporter__schools__pk'
    SCHOOL_NAME = 'submission__connection__contact__emisreporter__schools__name'

    def total_attribute_by_school(self, report, keyword, single_week=False):
        start_date = report.start_date
        if single_week:
            start_date = report.end_date - datetime.timedelta(7)
        return XFormSubmissionValue.objects.exclude(submission__has_errors=True)\
            .exclude(submission__connection__contact=None)\
            .filter(created__range=(start_date, report.end_date))\
            .filter(attribute__slug__in=keyword)\
            .filter(submission__connection__contact__emisreporter__schools__location__in=report.location.get_descendants(include_self=True).all())\
            .values(self.SCHOOL_NAME,
                    self.SCHOOL_ID)\
            .annotate(Sum('value_int'))

    def total_dateless_attribute_by_school(self, report, keyword):
        return XFormSubmissionValue.objects.exclude(submission__has_errors=True)\
            .exclude(submission__connection__contact=None)\
            .filter(attribute__slug__in=keyword)\
            .filter(submission__connection__contact__emisreporter__schools__location__in=report.location.get_descendants(include_self=True).all())\
            .values(self.SCHOOL_NAME,
                    self.SCHOOL_ID)\
            .annotate(Sum('value_int'))


    def num_weeks(self, report):
        if report.end_date == report.start_date:
            report.end_date = report.end_date + datetime.timedelta(days=1)
        td = report.end_date - report.start_date
        holidays = getattr(settings, 'SCHOOL_HOLIDAYS', [])
        for start, end in holidays:
            if start > report.start_date and end < report.end_date:
                td -= (end - start)

#        return td.days / 7
        return td.days / 7 if td.days / 7 > 1 else 1


class AverageSubmissionBySchoolColumn(Column, SchoolMixin):
    def __init__(self, keyword, extra_filters=None):
        self.keyword = keyword
        self.extra_filters = extra_filters

    def add_to_report(self, report, key, dictionary):
        val = total_submissions(self.keyword, report.start_date, report.end_date, report.location, self.extra_filters)
        for rdict in val:
            rdict['value'] = rdict['value'] / Location.objects.get(pk=rdict['location_id']).get_descendants(include_self=True).aggregate(Count('schools'))['schools__count']
        reorganize_location(key, val, dictionary)


class DateLessRatioColumn(Column, SchoolMixin):
    """
    This divides the total number of an indicator (for instance, boys yearly enrollment)  
    by the total of another indicator (for instance, total classrooms)].
    
    This gives you the ratio between the two indicators, each of which
    are fixed yearly amounts (not dependent on date).
    """
    def __init__(self, top_attrib, bottom_attrib):
        if type(top_attrib) != list:
            top_attrib = [top_attrib]
        if type(bottom_attrib) != list:
            bottom_attrib = [bottom_attrib]
        self.top_attrib = top_attrib
        self.bottom_attrib = bottom_attrib

    def add_to_report(self, report, key, dictionary):
        top_val = self.total_dateless_attribute_by_school(report, self.top_attrib)
        bottom_val = self.total_dateless_attribute_by_school(report, self.bottom_attib)

        bottom_dict = {}
        reorganize_dictionary('bottom', bottom_val, bottom_dict, self.SCHOOL_ID, self.SCHOOL_NAME, 'value_int__sum')
        val = []
        for rdict in top_val:
            if rdict[self.SCHOOL_ID] in bottom_dict:
                rdict['value_int__sum'] = (float(rdict['value_int__sum']) / bottom_dict[rdict[self.SCHOOL_ID]]['bottom'])
                val.append(rdict)

        reorganize_dictionary(key, val, dictionary, self.SCHOOL_ID, self.SCHOOL_NAME, 'value_int__sum')


class TotalAttributeBySchoolColumn(Column, SchoolMixin):

    def __init__(self, keyword, extra_filters=None):
        if type(keyword) != list:
            keyword = [keyword]
        self.keyword = keyword
        self.extra_filters = extra_filters

    def add_to_report(self, report, key, dictionary):
        val = self.total_attribute_by_school(report, self.keyword)
        reorganize_dictionary(key, val, dictionary, self.SCHOOL_ID, self.SCHOOL_NAME, 'value_int__sum')


class WeeklyAttributeBySchoolColumn(Column, SchoolMixin):

    def __init__(self, keyword, extra_filters=None):
        if type(keyword) != list:
            keyword = [keyword]
        self.keyword = keyword
        self.extra_filters = extra_filters

    def add_to_report(self, report, key, dictionary):
        val = self.total_attribute_by_school(report, self.keyword)
        num_weeks = self.num_weeks(report)
        for rdict in val:
            rdict['value_int__sum'] /= num_weeks
        reorganize_dictionary(key, val, dictionary, self.SCHOOL_ID, self.SCHOOL_NAME, 'value_int__sum')


class WeeklyPercentageColumn(Column, SchoolMixin):
    """
    This divides the total number of an indicator for one week (such as, boys weekly attendance) 
    by the total of another indicator (for instance, boys yearly enrollment)].
    
    This gives you the % expected for two indicators, 
    one that is reported on weekly (for the CURRENT WEEK)
    and the other which is a fixed total number.
    
    If invert is True, this column will evaluate to 100% - the above value.
    
    For example, if boys weekly attendance this week was 75%, setting invert to
    True would instead return 100 - 75 = 25%
    """
    def __init__(self, week_attrib, total_attrib, invert=False):
        if type(week_attrib) != list:
            week_attrib = [week_attrib]
        if type(total_attrib) != list:
            total_attrib = [total_attrib]
        self.week_attrib = week_attrib
        self.total_attrib = total_attrib
        self.invert = invert

    def add_to_report(self, report, key, dictionary):
        top_val = self.total_attribute_by_school(report, self.week_attrib, single_week=True)
        bottom_val = self.total_dateless_attribute_by_school(report, self.total_attrib)

        bottom_dict = {}
        reorganize_dictionary('bottom', bottom_val, bottom_dict, self.SCHOOL_ID, self.SCHOOL_NAME, 'value_int__sum')
        val = []
        for rdict in top_val:
            if rdict[self.SCHOOL_ID] in bottom_dict:
                rdict['value_int__sum'] = (float(rdict['value_int__sum']) / bottom_dict[rdict[self.SCHOOL_ID]]['bottom']) * 100
                if self.invert:
                    rdict['value_int__sum'] = 100 - rdict['value_int__sum']
                val.append(rdict)

        reorganize_dictionary(key, val, dictionary, self.SCHOOL_ID, self.SCHOOL_NAME, 'value_int__sum')


class AverageWeeklyTotalRatioColumn(Column, SchoolMixin):
    """
    This divides the total number of an indicator (such as, boys weekly attendance) by:
    [the number of non-holiday weeks in the date range * the total of another indicator
    (for instance, boys yearly enrollment)].
    
    This gives you the % expected for two indicators, one that is reported on weekly
    and the other which is a fixed total number.
    """
    def __init__(self, weekly_attrib, total_attrib):
        if type(weekly_attrib) != list:
            weekly_attrib = [weekly_attrib]
        if type(total_attrib) != list:
            total_attrib = [total_attrib]
        self.weekly_attrib = weekly_attrib
        self.total_attrib = total_attrib

    def add_to_report(self, report, key, dictionary):
        top_val = self.total_attribute_by_school(report, self.weekly_attrib)
        bottom_val = self.total_dateless_attribute_by_school(report, self.total_attrib)
        num_weeks = self.num_weeks(report)

        bottom_dict = {}
        reorganize_dictionary('bottom', bottom_val, bottom_dict, self.SCHOOL_ID, self.SCHOOL_NAME, 'value_int__sum')
        val = []
        for rdict in top_val:
            if rdict[self.SCHOOL_ID] in bottom_dict:
                rdict['value_int__sum'] = (float(rdict['value_int__sum']) / (bottom_dict[rdict[self.SCHOOL_ID]]['bottom'] * num_weeks)) * 100
                val.append(rdict)

        reorganize_dictionary(key, val, dictionary, self.SCHOOL_ID, self.SCHOOL_NAME, 'value_int__sum')


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


class AttendanceReport(SchoolReport):
    boys = WeeklyAttributeBySchoolColumn(["boys_%s" % g for g in GRADES])
    girls = WeeklyAttributeBySchoolColumn(["girls_%s" % g for g in GRADES])
    total_students = WeeklyAttributeBySchoolColumn((["girls_%s" % g for g in GRADES] + ["boys_%s" % g for g in GRADES]))
    percentage_students = AverageWeeklyTotalRatioColumn((["girls_%s" % g for g in GRADES] + ["boys_%s" % g for g in GRADES]), (["enrolledg_%s" % g for g in GRADES] + ["enrolledb_%s" % g for g in GRADES]))
    week_attrib = ["girls_%s" % g for g in GRADES] + ["boys_%s" % g for g in GRADES]
    total_attrib = ["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]
    percentange_student_absentism = WeeklyPercentageColumn(week_attrib, total_attrib, True)
    male_teachers = WeeklyAttributeBySchoolColumn("teachers_m")
    female_teachers = WeeklyAttributeBySchoolColumn("teachers_f")
    total_teachers = WeeklyAttributeBySchoolColumn(["teachers_f", "teachers_m"])
    percentage_teacher = AverageWeeklyTotalRatioColumn(["teachers_f", "teachers_m"], ["deploy_f", "deploy_m"])
    week_attrib = ["teachers_f", "teachers_m"]
    total_attrib = ["deploy_f", "deploy_m"]
    percentange_teachers_absentism = WeeklyPercentageColumn(week_attrib, total_attrib, True)


class AbuseReport(SchoolReport):
    cases = TotalAttributeBySchoolColumn("gemabuse_cases")
    
class KeyRatiosReport(SchoolReport):
    top_attrib = ["girls_%s" % g for g in GRADES] + ["boys_%s" % g for g in GRADES] 
    bottom_attrib = ["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]
    pupils_to_teacher = DateLessRatioColumn(top_attrib, bottom_attrib)

def location_values(location, data_dicts):
    for dict in data_dicts:
        if dict['location_name'] == location.name:
            if dict['value']:
                return dict['value']
            else:
                return '-'

def attendance_stats(request, district_id=None):
    stats = []
    user_location = Location.objects.get(pk=district_id) if district_id else get_location_for_user(request.user)
    if user_location == Location.tree.root_nodes()[0]:
        user_location = Location.objects.get(name='Kaabong')
    location = Location.tree.root_nodes()[0]
    start_date, end_date = previous_calendar_week()
    dates = {'start':start_date, 'end':end_date}
#    import pdb;pdb.set_trace()
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

def enrollment_stats(request, district_id=None):
    stats = []
    user_location = Location.objects.get(pk=district_id) if district_id else get_location_for_user(request.user)
    if user_location == Location.tree.root_nodes()[0]:
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

def headteacher_attendance_stats(request, district_id=None):
    stats = []
    user_location = Location.objects.get(pk=district_id) if district_id else get_location_for_user(request.user)
    if user_location == Location.tree.root_nodes()[0]:
        user_location = Location.objects.get(name='Kaabong')
    location = Location.tree.root_nodes()[0]
    start_date, end_date = previous_calendar_month()
    dates = {'start':start_date, 'end':end_date}
    values = total_submissions("gemteachers_htpresent", start_date=start_date, end_date=end_date, location=location, extra_filters={'eav__gemteachers_htpresent':1})
    stats.append(('head teacher attendance', location_values(user_location, values)))
    stats.append(('total head teacher deployment', Location.objects.get(pk=user_location.pk).get_descendants(include_self=True).aggregate(Count('schools'))['schools__count']))
    if Location.objects.get(pk=user_location.pk).get_descendants(include_self=True).aggregate(Count('schools'))['schools__count'] > 0:
        perc = values.count() / Location.objects.get(pk=user_location.pk).get_descendants(include_self=True).aggregate(Count('schools'))['schools__count'] * 100
    else:
        perc = 0
    res = {}
    res['dates'] = dates
    res['stats'] = stats
    return res

def abuse_stats(request, district_id=None):
    stats = []
    user_location = Location.objects.get(pk=district_id) if district_id else get_location_for_user(request.user)
    if user_location == Location.tree.root_nodes()[0]:
        user_location = Location.objects.get(name='Kaabong')
    location = Location.tree.root_nodes()[0]
    start_date, end_date = previous_calendar_month()
    dates = {'start':start_date, 'end':end_date}
    values = total_attribute_value("gemabuse_cases", start_date=start_date, end_date=end_date, location=location)
    stats.append(('GEM abuse cases', location_values(user_location, values)))
    res = {}
    res['dates'] = dates
    res['stats'] = stats
    return res

def keyratios_stats(request, district_id=None):
    stats = {}
    user_location = Location.objects.get(pk=district_id) if district_id else get_location_for_user(request.user)
    if user_location == Location.tree.root_nodes()[0]:
        user_location = Location.objects.get(name='Kaabong')
    location = Location.tree.root_nodes()[0]
    start_date = datetime.datetime(datetime.datetime.now().year, 1, 1)
    end_date = datetime.datetime.now()
    dates = {'start':start_date, 'end':end_date}
    top_attrib = ["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]
    bottom_attrib = ["deploy_f", "deploy_m"]
    total_pupils = XFormSubmissionValue.objects.exclude(submission__has_errors=True)\
            .exclude(submission__connection__contact=None)\
            .filter(created__range=(start_date, end_date))\
            .filter(attribute__slug__in=top_attrib)\
            .filter(submission__connection__contact__emisreporter__schools__location__in=user_location.get_descendants(include_self=True).all())\
            .annotate(Sum('value_int')).values_list('value_int__sum', flat=True)
    total_teachers = XFormSubmissionValue.objects.exclude(submission__has_errors=True)\
            .exclude(submission__connection__contact=None)\
            .filter(created__range=(start_date, end_date))\
            .filter(attribute__slug__in=bottom_attrib)\
            .filter(submission__connection__contact__emisreporter__schools__location__in=user_location.get_descendants(include_self=True).all())\
            .annotate(Sum('value_int')).values_list('value_int__sum', flat=True)
    if sum(total_teachers) > 0:
        stats['Pupil to Teacher Ratio'] = sum(total_pupils) / sum(total_teachers)
    else:
        stats['Pupil to Teacher Ratio'] = 'Not Available' 
    return stats
    

