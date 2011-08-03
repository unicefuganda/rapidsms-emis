from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from rapidsms.contrib.locations.models import Location
from django.views.decorators.cache import cache_control
from django.http import HttpResponseRedirect, HttpResponse
from .utils import total_submissions, total_attribute_value, reorganize_location, reorganize_timespan, GROUP_BY_WEEK, GROUP_BY_MONTH, GROUP_BY_DAY, GROUP_BY_QUARTER, get_group_by, flatten_location_list
from education.forms import DateRangeForm
import datetime
import time
from django.utils.datastructures import SortedDict
from rapidsms_xforms.models import XFormSubmission, XFormSubmissionValue
from rapidsms.models import Contact
import re
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from django.db import connection

Num_REG = re.compile('\d+')


def get_dates(request):
    """
    Process date variables from POST
    """
    if request.POST:
        form = DateRangeForm(request.POST)
        if form.is_valid():
            cursor = connection.cursor()
            cursor.execute("select min(created) from rapidsms_xforms_xformsubmission")
            min_date = cursor.fetchone()[0]
            start_date = form.cleaned_data['start']
            end_date = form.cleaned_data['end']
            request.session['start_date'] = start_date
            request.session['end_date'] = end_date
    elif request.GET.get('start_date', None) and request.GET.get('end_date', None):
        start_date = datetime.datetime.fromtimestamp(int(request.GET['start_date']))
        end_date = datetime.datetime.fromtimestamp(int(request.GET['end_date']))
        request.session['start_date'] = start_date
        request.session['end_date'] = end_date
        return {'start':start_date, 'end':end_date}
    else:
        form = DateRangeForm()
        cursor = connection.cursor()
        cursor.execute("select min(created), max(created) from rapidsms_xforms_xformsubmission")
        min_date, end_date = cursor.fetchone()
        start_date = end_date - datetime.timedelta(days=30)
        if request.GET.get('date_range', None):
            start_date, end_date = TIME_RANGES[request.GET.get('date_range')]()
            request.session['start_date'], request.session['end_date'] = start_date, end_date
        if request.session.get('start_date', None)  and request.session.get('end_date', None):
            start_date = request.session['start_date']
            end_date = request.session['end_date']

    return {'start':start_date, 'end':end_date, 'min':min_date, 'form':form}


def report(request):
    dates = get_dates(request)
    max_date = datetime.datetime.now()

    location = Location.tree.root_nodes()[0]

    if not location.get_children():
        return HttpResponse(status=400)

    start_date = dates['start']
    end_date = dates['end']

    report_dict = SortedDict()

    print str(total_attribute_value('boys_p1', start_date, end_date, location).query)

    for i in [1, 2, 4, 7]:
        rprt = total_attribute_value('boys_p%d' % i, start_date, end_date, location)
        reorganize_location('boys_p%d' % i, rprt, report_dict)
        rprt = total_attribute_value('girls_p%d' % i, start_date, end_date, location)
        reorganize_location('girls_p%d' % i, rprt, report_dict)

    rprt = total_attribute_value('deploy_m', start_date, end_date, location)
    reorganize_location('deploy_m', rprt, report_dict)
    rprt = total_attribute_value('deploy_f', start_date, end_date, location)
    reorganize_location('deploy_f', rprt, report_dict)

    rprt = total_attribute_value('gemabuse_cases', start_date, end_date, location)
    reorganize_location('gemabuse_cases', rprt, report_dict)

    rprt = total_attribute_value('classrooms_p4', start_date, end_date, location)
    reorganize_location('classrooms_p4', rprt, report_dict)
    return flatten_location_list(report_dict)


def index(request, location_id=None):
    """
        This is the basic stats page.  You can see that each column requires a separate
        call to report, but only once per column, not once per-column-per-location (same
        with the chart, no calls per week, month or quarter.

        FIXME: the proper GROUP_BY_xxx flags need to be used based on the date range
        passed from the user: If it's greater than nine months, it should probably
        be graphed quarterly, if it's greated than 3 months, monthly, if it's greater
        than 21 days, weekly, otherwise daily.
    """

    dates = get_dates(request)
    max_date = datetime.datetime.now()

    if location_id:
        location = get_object_or_404(Location, pk=location_id)
    else:
        location = Location.tree.root_nodes()[0]

    if not location.get_children():
        return HttpResponse(status=400)

    chart = request.session.get('stats', None)
    if chart :

        chart_path = Num_REG.sub(str(location.pk), chart).rsplit("?")[0] + "?start_date=%d&end_date=%d" % (time.mktime(dates['start'].timetuple()) , time.mktime(dates['end'].timetuple()))
        request.session['stats'] = chart_path
    else:
        request.session['stats'] = mark_safe("/cvs/charts/" + str(location.pk) + "/muac/?start_date=%d&end_date=%d" % (time.mktime(dates['start'].timetuple()) , time.mktime(dates['end'].timetuple())))
    start_date = dates['start']
    end_date = dates['end']

    report_dict = SortedDict()

    for i in [1, 2, 4, 7]:
        rprt = total_attribute_value('boys_p%d' % i, start_date, end_date, location)
        reorganize_location('boys_p%d' % i, rprt, report_dict)
        rprt = total_attribute_value('girls_p%d' % i, start_date, end_date, location)
        reorganize_location('girls_p%d' % i, rprt, report_dict)

    rprt = total_attribute_value('deploy_m', start_date, end_date, location)
    reorganize_location('deploy_m', rprt, report_dict)
    rprt = total_attribute_value('deploy_f', start_date, end_date, location)
    reorganize_location('deploy_f', rprt, report_dict)

    rprt = total_attribute_value('gemabuse_cases', start_date, end_date, location)
    reorganize_location('gemabuse_cases', rprt, report_dict)

    rprt = total_attribute_value('classrooms_p4', start_date, end_date, location)
    reorganize_location('classrooms_p4', rprt, report_dict)

    # label, link, colspan
    topColumns = (('', '', 1),
                  ('P1', '#', 2),
                  ('P2', '#', 2),
                  ('P4', '#', 2),
                  ('P7', '#', 2),
                  ('Teachers', '#', 2),
                  ('Abuse', '#', 1),
                  ('Classrooms', '#', 1),
                  )

#    chart_root = "loadChart('../" + ("../" if location_id else "")
#    charts_root = chart_root + "charts/" + str(location.pk)
    columns = (
        ('', '', 1, ''),
#               ('Total New Cases', 'javascript:void(0)', 1, charts_root + "/muac/')"),
        ('boys enrolled', '', 1, ''),
        ('girls enrolled', '', 1, ''),
        ('boys enrolled', '', 1, ''),
        ('girls enrolled', '', 1, ''),
        ('boys enrolled', '', 1, ''),
        ('girls enrolled', '', 1, ''),
        ('boys enrolled', '', 1, ''),
        ('girls enrolled', '', 1, ''),
        ('males deployed', '', 1, ''),
        ('females deployed', '', 1, ''),
        ('reported incidents', '', 1, ''),
        ('total for p4', '', 1, ''),
    )
    return render_to_response("education/stats.html",
                              {'report':report_dict,
                               'top_columns':topColumns,
                               'columns':columns,
                               'location_id':location_id,
                               'report_template':'education/partials/stats_main.html',
                               'start_date':dates['start'],
                               'end_date':dates['end'],
                               # timestamps in python are in seconds,
                               # in javascript they're in milliseconds
                               'max_ts':time.mktime(max_date.timetuple()) * 1000,
                               'min_ts':time.mktime(dates['min'].timetuple()) * 1000,
                               'start_ts':time.mktime(dates['start'].timetuple()) * 1000,
                               'end_ts':time.mktime(dates['end'].timetuple()) * 1000,
                               'date_range_form':dates['form'],
                               'page':'stats',
                                }, context_instance=RequestContext(request))

