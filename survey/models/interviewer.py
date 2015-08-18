import datetime
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from survey.interviewer_configs import LEVEL_OF_EDUCATION, LANGUAGES, COUNTRY_PHONE_CODE
from survey.models.base import BaseModel
from survey.models.access_channels import USSDAccess, ODKAccess
from survey.models.surveys import Survey


class Interviewer(BaseModel):
    MALE = '1'
    FEMALE = '0'
    name = models.CharField(max_length=100, blank=False, null=False)
    gender = models.CharField(default=MALE, verbose_name="Sex", choices=[(MALE, "M"), (FEMALE, "F")], max_length=10)
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(50)], null=True)
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    is_blocked = models.BooleanField(default=False)
    ea = models.ForeignKey('EnumerationArea', null=True, related_name="interviewers", verbose_name='Enumeration Area')
    language = models.CharField(max_length=100, null=True, choices=LANGUAGES,
                                blank=False, default='English', verbose_name="Preferred language of communication")
    weights = models.FloatField(default=0, blank=False)

    class Meta:
        app_label = 'survey'
        
    @property
    def ussd_access(self):
        return USSDAccess.objects.filter(interviewer=self)

    @property
    def odk_access(self):
        return ODKAccess.objects.filter(interviewer=self)
    
    def get_ussd_access(self, mobile_number):
        return USSDAccess.objects.get(interviewer=self, user_identifier=mobile_number)

    def get_odk_access(self, identifier):
        return ODKAccess.objects.get(interviewer=self, user_identifier=identifier)
    
    def present_households(self, survey=None):
        if survey is None:
            return self.registered_households.filter(ea=self.ea)
        else:
            return self.registered_households.filter(ea=self.ea, survey=survey)
    
    def generate_survey_households(self, survey):
        if survey.has_sampling:
            #random select households as per sample size
            pass
        else:
            return present_households(survey)

class SurveyAllocation(BaseModel):
    interviewer = models.ForeignKey(Interviewer, related_name='assignments')
    survey = models.ForeignKey(Survey, related_name='work_allocation')
    completed = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'survey'
    
    @classmethod
    def get_allocation(cls, interviewer):
        try:
            return cls.objects.get(interviewer=interviewer, completed=False).survey
        except cls.DoesNotExist:
            #allocate next unalocated survey
            open_surveys = interviewer.ea.open_surveys()
            allocated_surveys = cls.objects.filter(survey__in=open_surveys)
            available = [survey for survey in open_surveys if survey not in allocated_surveys]
            if available:
                survey = available[0]
                cls.object.create(interviewer=interviewer, survey=survey)
                return survey
        return None