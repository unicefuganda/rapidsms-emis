from django import forms
import datetime
from mptt.forms import TreeNodeChoiceField
from rapidsms.contrib.locations.models import Location
from generic.forms import ActionForm, FilterForm, ModuleForm
from mptt.forms import TreeNodeChoiceField
from rapidsms.contrib.locations.models import Location
from .models import School, EmisReporter
from rapidsms_xforms.models import XFormSubmissionValue
from django.contrib.auth.models import Group, User
from django.db.models import Q
from uganda_common.forms import SMSInput
from django.conf import settings
from rapidsms_httprouter.models import Message
from django.contrib.sites.models import Site
from contact.models import MassText
from rapidsms.models import Connection

date_range_choices = (('w', 'Previous Calendar Week'), ('m', 'Previous Calendar Month'), ('q', 'Previous calendar quarter'),)

class DateRangeForm(forms.Form): # pragma: no cover
    start = forms.IntegerField(required=True, widget=forms.HiddenInput())
    end = forms.IntegerField(required=True, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = self.cleaned_data

        start_ts = cleaned_data.get('start')
        cleaned_data['start'] = datetime.datetime.fromtimestamp(float(start_ts))

        end_ts = cleaned_data.get('end')
        cleaned_data['end'] = datetime.datetime.fromtimestamp(float(end_ts))
        return cleaned_data

AREAS = Location.tree.all().select_related('type')

class ReporterFreeSearchForm(FilterForm):

    """ concrete implementation of filter form
        TO DO: add ability to search for multiple search terms separated by 'or'
    """

    search = forms.CharField(max_length=100, required=False, label="Free-form search",
                             help_text="Use 'or' to search for multiple names")
    
    def filter(self, request, queryset):
        search = self.cleaned_data['search']
        if search == "":
            pass
        else:
            if search[:3] == '256':
                search = search[3:]
            elif search[:1] == '0':
                search = search[1:]
            queryset = queryset.filter(Q(name__icontains=search) | Q(reporting_location__name__icontains=search) | Q(connection__identity__icontains=search) | Q(schools__name__icontains=search)).distinct()    
        return queryset

class SchoolFilterForm(FilterForm):
    """ filter form for emis schools """
    school = forms.ChoiceField(choices=(('', '-----'), (-1, 'Has No School'),) + tuple(School.objects.values_list('pk', 'name').order_by('name')))


    def filter(self, request, queryset):
        school_pk = self.cleaned_data['school']
        if school_pk == '':
            return queryset
        elif int(school_pk) == -1:
            return queryset.filter(schools__name=None)
        else:
            return queryset.filter(schools=school_pk)

class NewConnectionForm(forms.Form):
    identity = forms.CharField(max_length=15, required=True, label="Primary contact information")

class EditReporterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
           super(EditReporterForm, self).__init__(*args, **kwargs)
           self.fields['reporting_location'] = TreeNodeChoiceField(queryset=self.fields['reporting_location'].queryset, level_indicator=u'.')

    class Meta:
        model = EmisReporter
        fields = ('name', 'reporting_location', 'groups', 'schools')

class DistrictFilterForm(forms.Form):
    """ filter form for districts """
    locs = Location.objects.filter(name__in=XFormSubmissionValue.objects.values_list('submission__connection__contact__reporting_location__name', flat=True))
    locs_list = []
    for loc in locs:
        if not Location.tree.root_nodes()[0].pk == loc.pk and loc.type.name == 'district':
            locs_list.append((loc.pk, loc.name))
    district = forms.ChoiceField(choices=(('', '-----'),) + tuple(locs_list))

class LimitedDistictFilterForm(FilterForm):

    """ filter Emis Reporters on their districts """

    locs = Location.objects.filter(name__in=XFormSubmissionValue.objects.values_list('submission__connection__contact__reporting_location__name', flat=True)).order_by('name')
    locs_list = []
    for loc in locs:
        if not Location.tree.root_nodes()[0].pk == loc.pk and loc.type.name == 'district':
            locs_list.append((loc.pk, loc.name))
    district = forms.ChoiceField(choices=(('', '-----'),) + tuple(locs_list))

    def filter(self, request, queryset):
        district_pk = self.cleaned_data['district']
        if district_pk == '':
            return queryset
        elif int(district_pk) == -1:
            return queryset.filter(reporting_location=None)
        else:

            try:
                district = Location.objects.get(pk=district_pk)
            except Location.DoesNotExist:
                district = None
            if district:
                return queryset.filter(reporting_location__in=district.get_descendants(include_self=True))
            else:
                return queryset

class RolesFilterForm(FilterForm):
    def __init__(self, data=None, **kwargs):
        self.request = kwargs.pop('request')
        if data:
            forms.Form.__init__(self, data, **kwargs)
        else:
            forms.Form.__init__(self, **kwargs)
        choices = ((-1, 'No Group'),) + tuple([(int(g.pk), g.name) for g in Group.objects.all().order_by('name')])
        self.fields['groups'] = forms.ChoiceField(choices=choices, required=True)


    def filter(self, request, queryset):
        groups_pk = self.cleaned_data['groups']
        if groups_pk == '-1':
            return queryset
        else:
            return queryset.filter(groups=groups_pk)

class SchoolForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SchoolForm, self).__init__(*args, **kwargs)
        self.fields['location'] = TreeNodeChoiceField(queryset=self.fields['location'].queryset, level_indicator=u'.')
        self.fields['name'] = forms.CharField(required=False, max_length=160)
        self.fields['emis_id'] = forms.CharField(required=False, max_length=10)

    class Meta:
        model = School
        fields = ('name', 'location', 'emis_id')

class FreeSearchSchoolsForm(FilterForm):

    """ concrete implementation of filter form
        TO DO: add ability to search for multiple search terms separated by 'or'
    """

    search = forms.CharField(max_length=100, required=False, label="Free-form search",
                             help_text="Use 'or' to search for multiple names")

    def filter(self, request, queryset):
        search = self.cleaned_data['search']
        if search == "":
            return queryset
        else:
            return queryset.filter(Q(name__icontains=search)
                                   | Q(emis_id__icontains=search)
                                   | Q(location__name__icontains=search))

class SchoolDistictFilterForm(FilterForm):

    """ filter Schools on their districts """

    locs = Location.objects.filter(name__in=School.objects.values_list('location__name', flat=True)).order_by('name')
    locs_list = []
    for loc in locs:
        if not Location.tree.root_nodes()[0].pk == loc.pk and loc.type.name == 'district':
            locs_list.append((loc.pk, loc.name))
    district = forms.ChoiceField(choices=(('', '-----'),) + tuple(locs_list))

    def filter(self, request, queryset):
        district_pk = self.cleaned_data['district']
        if district_pk == '':
            return queryset
        elif int(district_pk) == -1:
            return queryset.filter(reporting_location=None)
        else:

            try:
                district = Location.objects.get(pk=district_pk)
            except Location.DoesNotExist:
                district = None
            if district:
                return queryset.filter(location__in=district.get_descendants(include_self=True))
            else:
                return queryset

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
                
class MassTextForm(ActionForm):

    text = forms.CharField(max_length=160, required=True, widget=SMSInput())
    action_label = 'Send Message'

    def clean_text(self):
        text = self.cleaned_data['text']

        #replace common MS-word characters with SMS-friendly characters
        for find, replace in [(u'\u201c', '"'),
                              (u'\u201d', '"'),
                              (u'\u201f', '"'),
                              (u'\u2018', "'"),
                              (u'\u2019', "'"),
                              (u'\u201B', "'"),
                              (u'\u2013', "-"),
                              (u'\u2014', "-"),
                              (u'\u2015', "-"),
                              (u'\xa7', "$"),
                              (u'\xa1', "i"),
                              (u'\xa4', ''),
                              (u'\xc4', 'A')]:
            text = text.replace(find, replace)
        return text

    def perform(self, request, results):
        if results is None or len(results) == 0:
            return ('A message must have one or more recipients!', 'error')

        if request.user and request.user.has_perm('auth.add_message'):
            connections = \
                list(Connection.objects.filter(contact__in=results).distinct())

            text = self.cleaned_data.get('text', "")
            text = text.replace('%', u'\u0025')

            messages = Message.mass_text(text, connections)

            MassText.bulk.bulk_insert(send_pre_save=False,
                    user=request.user,
                    text=text,
                    contacts=list(results))
            masstexts = MassText.bulk.bulk_insert_commit(send_post_save=False, autoclobber=True)
            masstext = masstexts[0]
            if settings.SITE_ID:
                masstext.sites.add(Site.objects.get_current())

            return ('Message successfully sent to %d numbers' % len(connections), 'success',)
        else:
            return ("You don't have permission to send messages!", 'error',)
        
class SchoolMassTextForm(ActionForm):

    text = forms.CharField(max_length=160, required=True, widget=SMSInput())
    action_label = 'Send Message'

    def clean_text(self):
        text = self.cleaned_data['text']

        #replace common MS-word characters with SMS-friendly characters
        for find, replace in [(u'\u201c', '"'),
                              (u'\u201d', '"'),
                              (u'\u201f', '"'),
                              (u'\u2018', "'"),
                              (u'\u2019', "'"),
                              (u'\u201B', "'"),
                              (u'\u2013', "-"),
                              (u'\u2014', "-"),
                              (u'\u2015', "-"),
                              (u'\xa7', "$"),
                              (u'\xa1', "i"),
                              (u'\xa4', ''),
                              (u'\xc4', 'A')]:
            text = text.replace(find, replace)
        return text

    def perform(self, request, results):
        if results is None or len(results) == 0:
            return ('A message must have one or more recipients!', 'error')

        if request.user and request.user.has_perm('auth.add_message'):
            reporters = []
            for school in results:
                for rep in school.emisreporter_set.filter(groups__name__in=['Teachers', 'Head Teachers']):
                    reporters.append(rep) 
            connections = \
                list(Connection.objects.filter(contact__in=reporters).distinct())

            text = self.cleaned_data.get('text', "")
            text = text.replace('%', u'\u0025')

            messages = Message.mass_text(text, connections)

            MassText.bulk.bulk_insert(send_pre_save=False,
                    user=request.user,
                    text=text,
                    contacts=list(reporters))
            masstexts = MassText.bulk.bulk_insert_commit(send_post_save=False, autoclobber=True)
            masstext = masstexts[0]
            if settings.SITE_ID:
                masstext.sites.add(Site.objects.get_current())

            return ('Message successfully sent to %d numbers' % len(connections), 'success',)
        else:
            return ("You don't have permission to send messages!", 'error',)

