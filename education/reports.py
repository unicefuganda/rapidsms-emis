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


class PollResultsColumn(Column):
    def __init__(self, poll_name):
        self.poll = Poll.objects.get(name=poll_name)

    def add_to_report(self, report, key, dictionary):
        val = self.poll.


class Report(object):
    def __init__(self, request=None):
        dates = get_dates(request)

        self.location = Location.tree.root_nodes()[0]
        self.start_date = dates['start']
        self.end_date = dates['end']

        self.report = {} #SortedDict()
        column_classes = Column.__subclasses__()
        for attrname in dir(self):
            val = getattr(self, attrname)
            if type(val) in column_classes:
                val.add_to_report(self, attrname, self.report)

        self.report = flatten_location_list(self.report)


    def __iter__(self):
        return self.report.__iter__()

    def __len__(self):
        return len(self.report)


class MainEmisReport(Report):
    boys_p1 = XFormAttributeColumn('boys_p1')
    boys_p2 = XFormAttributeColumn('boys_p2')
    boys_p4 = XFormAttributeColumn('boys_p4')
    boys_p7 = XFormAttributeColumn('boys_p7')

    girls_p1 = XFormAttributeColumn('girls_p1')
    girls_p2 = XFormAttributeColumn('girls_p2')
    girls_p4 = XFormAttributeColumn('girls_p4')
    girls_p7 = XFormAttributeColumn('girls_p7')

    deploy_m = XFormAttributeColumn('deploy_m')
    deploy_f = XFormAttributeColumn('deploy_f')

    gemabuse_cases = XFormAttributeColumn('gemabuse_cases')
    classrooms_p4 = XFormAttributeColumn('classrooms_p4')
