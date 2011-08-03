from django import forms
import datetime
from mptt.forms import TreeNodeChoiceField
from rapidsms.contrib.locations.models import Location
from generic.forms import ActionForm, FilterForm, ModuleForm
from mptt.forms import TreeNodeChoiceField
from rapidsms.contrib.locations.models import Location
from .models import School

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

class SchoolFilterForm(FilterForm):
    """ filter form for emis schools """
    school = forms.ChoiceField(choices=(('', '-----'), (-1, 'Has No School'),) + tuple(School.objects.values_list('pk', 'name').order_by('name')))


    def filter(self, request, queryset):
        school_pk = self.cleaned_data['school']
        if school_pk == '':
            return queryset
        elif int(school_pk) == -1:
            return queryset.filter(school=None)
        else:
            return queryset.filter(school=school_pk)
