from django.db import connection
from django.template import RequestContext
from education.forms import DateRangeForm
import datetime
import re
import time

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



