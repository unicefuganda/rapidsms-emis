from .utils import total_submissions, reorganize_location, flatten_location_list, total_attribute_value
from .views import get_dates
from rapidsms.contrib.locations.models import Location

class Column(object):
    def add_to_report(self, report, key, dictionary):
        pass

class XFormSubmissionColumn(Column):
    def __init__(self, keyword, extra_filters=None):
        self.keyword = keyword
        self.extra_filters = extra_filters

    def add_to_report(self, report, key, dictionary):
        val = total_submissions(self.keyword, report.start_date, report.end_date, report.location, self.extra_filters)
        reorganize_location(key, val, dictionary)


class XFormAttributeColumn(Column):
    def __init__(self, keyword, extra_filters=None):
        self.keyword = keyword
        self.extra_filters = extra_filters

    def add_to_report(self, report, key, dictionary):
        val = total_attribute_value(self.keyword, report.start_date, report.end_date, report.location, self.extra_filters)
        reorganize_location(key, val, dictionary)


class PollNumericResultsColumn(Column):

    AVERAGE = 1
    MAX = 2
    MIN = 4
    COUNT = 8
    STDDEV = 16
    SUM = 32

    VALUE_FLAGS = [(AVERAGE, 'avg'),
                   (MAX, 'max'),
                   (MIN, 'min'),
                   (COUNT, 'count'),
                   (STDDEV, 'stddev'),
                   (SUM, 'sum')]

    def __init__(self, poll_name, attrs=SUM):
        self.poll = Poll.objects.get(name=poll_name)
        self.attrs = attrs

    def add_to_report(self, report, key, dictionary):
        var = poll.get_numeric_report_data(location=report.location)
        for dict in var:
            loc_name = dict['location_name']
            dictionary.setdefault(loc_name, {'location_id':dict['location_id'], 'diff':(dict['rght'] - dict['lft'])})
            report.columns = report.columns[0:len(report._columns) - 1]
            for flag, attrkey in VALUE_FLAGS:
                if self.attrs & flag:
                    dictionary[loc_name]["%s_%s" % (key, attrkey)] = dict["value_float__%s" % attrkey]
                    report.columns.append("%s_%s" % (key, attrkey))


class PollCategoryResultsColumn(Column):

    def __init__(self, poll, category):
        self.poll = Poll.obects.get(name=poll_name)
        self.category = Category.objects.get(poll=self.poll, name=category)

    def add_to_report(self, report, key, dictionary):
        var = poll.responses_by_category(location=report.location)
        if len(var):
            location_name = var[0]['location_name']
            total = 0
            category_dict = {}
            for dict in var:
                if dict['location_name'] == location_name:
                    dictionary.setdefault(location_name, {'location_id':dict['location_id'], 'diff':(dict['rght'] - dict['lft'])})
                    category_dict[dict['category__name']] = dict['value']
                    total = total + dict['value']
                else:
                    dictionary[location_name][key] = (category_dict[self.category] if self.category.name in category_dict else 0) / total
                    location_name = dict['location_name']
                    dictionary.setdefault(location_name, {'location_id':dict['location_id'], 'diff':(dict['rght'] - dict['lft'])})
                    category_dict = {}
                    category_dict[dict['category__name']] = dict['value']
                    total = dict['value']
            dictionary[location_name][key] = (category_dict[self.category] if self.category.name in category_dict else 0) / total


class Report(object):
    def __init__(self, request=None):
        dates = get_dates(request)

        self.location = Location.tree.root_nodes()[0]
        self.start_date = dates['start']
        self.end_date = dates['end']

        self.report = {} #SortedDict()
        self.columns = []
        column_classes = Column.__subclasses__()
        for attrname in dir(self):
            val = getattr(self, attrname)
            if type(val) in column_classes:
                self.columns.append(attrname)
                val.add_to_report(self, attrname, self.report)

        self.report = flatten_location_list(self.report)


    def __iter__(self):
        return self.report.__iter__()

    def __len__(self):
        return len(self.report)


class MainEmisReport(Report):
    boys_p3 = XFormAttributeColumn('boys_p3')
    girls_p3 = XFormAttributeColumn('girls_p3')

    boys_p5 = XFormAttributeColumn('boys_p5')
    girls_p5 = XFormAttributeColumn('girls_p5')

    deploy_m = XFormAttributeColumn('deploy_m')
    deploy_f = XFormAttributeColumn('deploy_f')

    gemabuse_cases = XFormAttributeColumn('gemabuse_cases')
    classrooms_p4 = XFormAttributeColumn('classrooms_p5')

class ClassRoomReport(Report):
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
