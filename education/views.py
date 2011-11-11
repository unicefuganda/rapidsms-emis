#from django.db import connection
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.contrib.auth.decorators import user_passes_test
from django import forms
from .forms import NewConnectionForm, EditReporterForm, DistrictFilterForm, SchoolForm
from .models import *
from uganda_common.utils import *
from rapidsms.contrib.locations.models import Location
from .reports import *
from .utils import *
from urllib2 import urlopen
import  re


Num_REG = re.compile('\d+')

super_user_required=user_passes_test(lambda u: u.groups.filter(name__in=['Admins','DFO']).exists() or u.is_superuser)
def index(request):
    return render_to_response("education/index.html", {}, RequestContext(request))

@login_required
def dashboard(request):
    profile = request.user.get_profile()
    if profile.is_member_of('DEO'):
        return deo_dashboard(request)
    else:
        return index(request)

def deo_dashboard(request):
    form = DistrictFilterForm()
    district_id = None
    if request.method == 'POST':
        form = DistrictFilterForm(request.POST)
        if form.is_valid():
            district_id = form.cleaned_data['district']
    user_location = Location.objects.get(pk=district_id) if district_id else get_location_for_user(request.user)
    top_node = Location.tree.root_nodes()[0]
    return render_to_response("education/deo/deo_dashboard.html", {\
                                'location':user_location,\
                                'top_node':top_node,\
                                'form':form, \
                                'alerts':deo_alerts(request, district_id),\
                                'keyratios':keyratios_stats(request, district_id),\
                                'attendance_stats':attendance_stats(request, district_id), \
                                'enrollment_stats':enrollment_stats(request, district_id), \
                                'headteacher_attendance_stats':headteacher_attendance_stats(request, district_id), \
                                'gem_htpresent_stats':gem_htpresent_stats(request, district_id), \
                                'abuse_stats':abuse_stats(request, district_id), \
                                }, RequestContext(request))

def whitelist(request):
    return render_to_response(
    "education/whitelist.txt",
    {'connections': Connection.objects.all()},
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

def _addto_autoreg(connections):
    for connection in connections:
        if not connection.contact and \
            not ScriptProgress.objects.filter(script__slug='emis_autoreg', connection=connection).count():
                        ScriptProgress.objects.create(script=Script.objects.get(slug="emis_autoreg"), \
                                              connection=connection)

@login_required
def add_connection(request):
    form = NewConnectionForm()
    if request.method == 'POST':
        form = NewConnectionForm(request.POST)
        connections = []
        if form.is_valid():
            identity = form.cleaned_data['identity']
            identity, backend = assign_backend(str(identity.strip()))
            connection, created = Connection.objects.get_or_create(identity=identity, backend=backend)
            connections.append(connection)
            other_numbers = request.POST.getlist('other_nums')
            if len(other_numbers) > 0:
                for number in other_numbers:
                    identity, backend = assign_backend(str(number.strip()))
                    connection, created = Connection.objects.get_or_create(identity=identity, backend=backend)
                    connections.append(connection)
            _addto_autoreg(connections)
            _reload_whitelists()
#            time.sleep(2)
            return render_to_response('education/partials/addnumbers_row.html', {'object':connections, 'selectable':False}, RequestContext(request))

    return render_to_response("education/partials/new_connection.html", {'form':form}, RequestContext(request))

@login_required
def delete_connection(request, connection_id):
    connection = get_object_or_404(Connection, pk=connection_id)
    connection.delete()
    _reload_whitelists()
    return render_to_response("education/partials/connection_view.html", {'object':connection.contact }, context_instance=RequestContext(request))

@login_required
def delete_reporter(request, reporter_pk):
    reporter = get_object_or_404(EmisReporter, pk=reporter_pk)
    if request.method == 'POST':
        reporter.delete()
    return HttpResponse(status=200)

@login_required
def edit_reporter(request, reporter_pk):
    reporter = get_object_or_404(EmisReporter, pk=reporter_pk)
    reporter_form = EditReporterForm(instance=reporter)
    if request.method == 'POST':
        reporter_form = EditReporterForm(instance=reporter,
                data=request.POST)
        if reporter_form.is_valid():
            reporter_form.save()
        else:
            return render_to_response('education/partials/edit_reporter.html'
                    , {'reporter_form': reporter_form, 'reporter'
                    : reporter},
                    context_instance=RequestContext(request))
        return render_to_response('/education/partials/reporter_row.html',
                                  {'object':EmisReporter.objects.get(pk=reporter_pk),
                                   'selectable':True},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('education/partials/edit_reporter.html',
                                  {'reporter_form': reporter_form,
                                  'reporter': reporter},
                                  context_instance=RequestContext(request))

@login_required
def add_schools(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        schools = []
        if form.is_valid():
            names = filter(None, request.POST.getlist('name'))
            locations = request.POST.getlist('location')
            emis_ids = request.POST.getlist('emis_id')
            if len(names) > 0:
                for i, name in enumerate(names):
                    location = Location.objects.get(pk=int(locations[i]))
                    emis_id = emis_ids[i]
                    name, created = School.objects.get_or_create(name=name, location=location, emis_id=emis_id)
                    schools.append(name)

                return render_to_response('education/partials/addschools_row.html', {'object':schools, 'selectable':False}, RequestContext(request))
    else:
        form = SchoolForm()
    return render_to_response('education/deo/add_schools.html',
                                  {'form': form,
                                }, context_instance=RequestContext(request))

@login_required
def delete_school(request, school_pk):
    school = get_object_or_404(School, pk=school_pk)
    if request.method == 'POST':
        school.delete()
    return HttpResponse(status=200)

@login_required
def edit_school(request, school_pk):
    school = get_object_or_404(School, pk=school_pk)
    school_form = SchoolForm(instance=school)
    if request.method == 'POST':
        school_form = SchoolForm(instance=school,
                data=request.POST)
        if school_form.is_valid():
            school_form.save()
        else:
            return render_to_response('education/partials/edit_school.html'
                    , {'school_form': school_form, 'school'
                    : school},
                    context_instance=RequestContext(request))
        return render_to_response('/education/partials/school_row.html',
                                  {'object':School.objects.get(pk=school_pk),
                                   'selectable':True},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('education/partials/edit_school.html',
                                  {'school_form': school_form,
                                  'school': school},
                                  context_instance=RequestContext(request))
        
@login_required
def school_detail(request, school_id):
    school = School.objects.get(id=school_id)
    last_submissions = school_last_xformsubmission(request, school_id)
    return render_to_response("education/school_detail.html", {\
                            'school': school,
                            'last_submissions': last_submissions,
                                }, RequestContext(request))


# analytics specific for emis {copy, but adjust to suit your needs}
@login_required
def to_excel(request,district_id=None):
    return create_excel_dataset(request, district_id)

@login_required
def excel_reports(req):
    return render_to_response('education/excelreports/excel_dashboard.html',{},RequestContext(req))

#visualization
#TODO add to dashboards or stats views {work on generic views}
#class ChartView(TemplateView):
#    # boys and girls attendance
#    context_object_name = "girl_boy_list"
#    from .utils import produce_curated_data
#    queryset = produce_curated_data()
#    template_name = "education/emis_chart.html"

@login_required
def attendance_chart(req): #consider passing date function nicely and use of slugs to pick specific data
    categories = "P1 P2 P3 P4 P5 P6 P7".split()
    boyslugs = ["boys_%s"%g for g in "p1 p2 p3 p4 p5 p6 p7".split()]
    girlslugs = ["girls_%s"%g for g in "p1 p2 p3 p4 p5 p6 p7".split()]
    from .reports import get_location, previous_calendar_week
    #user_location = get_location(request, district_id)
    user_location = Location.objects.get(pk=1)

    ## Limited number of schools by 25
    schools = School.objects.filter(location__in=user_location.get_descendants(include_self=True).all())[:25]
    date_tup = previous_calendar_week()
    kw = ('start','end')
    dates = dict(zip(kw,date_tup))

    #TODO include date filtering for more than 1week {need a use-case}

    boy_values = XFormSubmissionValue.objects.exclude(submission__has_errors=True)\
                .filter(attribute__slug__in=boyslugs)\
                .filter(submission__connection__contact__emisreporter__schools__in=schools)\
                .values('submission__connection__contact__emisreporter__schools__name')\
                .values_list('submission__connection__contact__emisreporter__schools__name','value_int')
                #.annotate(Avg('value_int'))
    
    girl_values = XFormSubmissionValue.objects.exclude(submission__has_errors=True)\
                .filter(attribute__slug__in=girlslugs)\
                .filter(submission__connection__contact__emisreporter__schools__in=schools)\
                .values('submission__connection__contact__emisreporter__schools__name')\
                .values_list('submission__connection__contact__emisreporter__schools__name','value_int')

    def cleanup(values):
        index = 0
        clean_val = []
        while index < len(values):
            school_values = []
            #school_values.append(values[index][0])
            school_values.append(values[index][1])
            for i in range(index,(index+6)):
                try:
                    school_values.append(values[i][1])
                except IndexError:
                    school_values.append(0)
                # cleanup
                school_values.reverse()
            index += 6
            clean_val.append(school_values)
        return clean_val

    schools = [school_name.name for school_name in schools]
    boy_attendance = {}
    girl_attendance = {}

    clean_boy_values = cleanup(boy_values)
    clean_girl_values = cleanup(girl_values)

    for school_name,school_boy_value_list,school_girl_value_list in zip(schools,clean_boy_values,clean_girl_values):
        boy_attendance[school_name]  = school_boy_value_list
        girl_attendance[school_name] = school_girl_value_list

    # use attendance dicts to populate attendance of folks in school
    return render_to_response('education/emis_chart.html',{
        'boy_attendance':boy_attendance.items(),
        'girl_attendance':girl_attendance.items(),
        'categories':categories,
        },RequestContext(req))


    
class UserForm(forms.ModelForm):
   
    location=forms.ModelChoiceField(queryset=Location.objects.filter(type__in=["district","country"]).order_by('name'),required=True)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput,required=False)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput,
        help_text = "Enter the same password as above, for verification.",required=False)

    class Meta:
        model = User
        fields = ("username","first_name","last_name", "groups","password1","password2")
    def __init__(self, *args, **kwargs):
        self.edit= kwargs.pop('edit',None)
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['groups'].help_text=""
        self.fields['groups'].required=True



    def clean_username(self):
        username = self.cleaned_data["username"]
        print self.edit
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        if not self.edit:
            raise forms.ValidationError("A user with that username already exists.")
        else:
            return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        
        password2 = self.cleaned_data.get("password2","")
        if password1 == password2 and password2 =="" and self.edit:
            return password2
        elif password2 =="":
            raise forms.ValidationError("This Field is Required")
        if password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        user = super(UserForm, self).save(commit=False)
        if self.edit and self.cleaned_data["password1"] != "":
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


@super_user_required
def edit_user(request, user_pk=None):
    title=""
    user=User()
    if request.method == 'POST':
        if user_pk:
            user = get_object_or_404(User, pk=user_pk)
        user_form = UserForm(request.POST,instance=user,edit=True)
        if user_form.is_valid():
            user = user_form.save()
            try:
                profile=UserProfile.objects.get(user=user)
                profile.location=user_form.cleaned_data['location']
                profile.role=Role.objects.get(pk=user.groups.all()[0].pk)
                profile.save()
            except UserProfile.DoesNotExist:

               
                UserProfile.objects.create(name=user.first_name,user=user,role=Role.objects.get(pk=user_form.cleaned_data['groups'][0].pk),location=user_form.cleaned_data['location'])

            return HttpResponseRedirect(reverse("emis_users"))

    elif user_pk:
        user = get_object_or_404(User, pk=user_pk)
        user_form = UserForm(instance=user,edit=True)
        title="Editing "+user.username

    else:
        user_form = UserForm(instance=user)
    
    return render_to_response('education/partials/edit_user.html', {'user_form': user_form,'title':title},
                              context_instance=RequestContext(request))

