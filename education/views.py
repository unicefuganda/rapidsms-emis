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



