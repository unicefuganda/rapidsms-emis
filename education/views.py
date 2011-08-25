#from django.db import connection
from .forms import NewConnectionForm
from .models import *
from django.conf import settings, settings, settings
from django.contrib.auth.decorators import login_required, login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms.util import ErrorList
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404, render_to_response, \
    redirect, get_object_or_404, render_to_response
from django.template import RequestContext, RequestContext
from django.views.decorators.http import require_GET, require_POST, require_GET, \
    require_POST
from poll.models import Poll, ResponseCategory, Response
from rapidsms.models import Connection, Contact, Contact, Connection
from rapidsms_httprouter.models import Message
from uganda_common.utils import get_dates, assign_backend
from urllib2 import urlopen, urlopen
import datetime
import datetime
import re
import time

Num_REG = re.compile('\d+')

def index(request):
    return render_to_response("education/index.html", {}, RequestContext(request))

def whitelist(request):
    return render_to_response(
    "education/whitelist.txt",
    {'connections': Connection.objects.filter(contact__in=Contact.objects.all()).distinct()},
    mimetype="text/plain",
    context_instance=RequestContext(request))

def _reload_whitelists():
    refresh_urls = getattr(settings, 'REFRESH_WHITELIST_URL', None)
    if refresh_urls is not None:
        if not type(refresh_urls) == list:
            refresh_urls = [refresh_urls, ]
        for refresh_url in refresh_urls:
            try:
                status_code = urlopen(refresh_url).getcode()
                if int(status_code / 100) == 2:
                    continue
                else:
                    return False
            except Exception as e:
                return False
        return True
    return False

@login_required
def add_connection(request):
    form = NewConnectionForm()
    if request.method == 'POST':
        form = NewConnectionForm(request.POST)
        connections = []
        if form.is_valid():
            identity = form.cleaned_data['identity']
            identity, backend = assign_backend(str(identity))
            connection, created = Connection.objects.get_or_create(identity=identity, backend=backend)
            connections.append(connection)
            other_numbers = request.POST.getlist('other_nums')
            if len(other_numbers) > 0:
                for number in other_numbers:
                    identity, backend = assign_backend(str(number))
                    connection, created = Connection.objects.get_or_create(identity=identity, backend=backend)
                    connections.append(connection)
            _reload_whitelists()
            return render_to_response('education/partials/addnumbers_row.html', {'object':connections, 'selectable':False}, RequestContext(request))

    return render_to_response("education/partials/new_connection.html", {'form':form}, RequestContext(request))

@login_required
def delete_connection(request, connection_id):
    connection = get_object_or_404(Connection, pk=connection_id)
    connection.delete()
    _reload_whitelists()
    return render_to_response("education/partials/connection_view.html", {'object':connection.contact }, context_instance=RequestContext(request))



