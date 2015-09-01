from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models.households import Household
from survey.models import WebAccess, Interviewer, SurveyAllocation
from django import forms

class HouseholdForm(ModelForm):

    class Meta:
        model = Household
        exclude = ['ea', 'survey', 'household_code']
        widgets = {
            'ea': forms.HiddenInput(),
            'registration_channel': forms.HiddenInput()
        }

    def __init__(self, is_edit=False, ea=None,  survey=None, *args, **kwargs):
        super(HouseholdForm, self).__init__(*args, **kwargs)
        self.is_editing = is_edit
        self.fields['registration_channel'].initial = WebAccess.choice_name()
        if ea is not None:
            self.fields['registrar'].queryset = Interviewer.objects.filter(ea__pk=ea)

#         if not self.is_editing:
#             self.fields['uid'].initial = Household.next_uid(survey)
#         else:
#             self.fields['uid'].initial = self.instance.uid
#             self.fields['uid'].widget.attrs['disabled'] = 'disabled'
    def clean_registrar(self):
        if SurveyAllocation.get_allocation(self.cleaned_data['registrar']) is None:
            raise ValidationError("No open survey available for this Interviewer yet.")
        return self.cleaned_data['registrar']

    def clean_house_number(self):
        if self.instance is None:
            try:
                house_number = self.cleaned_data['house_number']
                household = Household.objects.filter(house_number=int(house_number))
                if household:
                    raise ValidationError("Household with this Household Number already exists.")
            except TypeError:
                raise ValidationError("This field is required.")
        return self.cleaned_data['house_number']