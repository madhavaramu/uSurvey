import json
from django.template.defaultfilters import slugify

from survey.tests.base_test import BaseTest
from django.test.client import Client
from mock import *
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import *
from survey.forms.household import *
from survey.views.household import *

class HouseholdViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_households')
        self.client.login(username='Rajni', password='I_Rock')

    def test_new_GET(self):
        some_type = LocationType.objects.create(name='some type', slug='some_name')
        uganda = Location.objects.create(name="Uganda", type=some_type)
        response = self.client.get('/households/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('households/new.html', templates)
        self.assertEquals(response.context['action'], '/households/new/')
        self.assertEquals(response.context['id'], 'create-household-form')
        self.assertEquals(response.context['button_label'], 'Create Household')
        self.assertEquals(response.context['loading_text'], 'Creating...')
        investigator_form = {'value': '', 'text': '', 'options': Investigator.objects.all(), 'error': ''}
        self.assert_dictionary_equal(response.context['investigator_form'], investigator_form)
        self.assertIsNotNone(response.context['householdform'])
        self.assertIsNotNone(response.context['headform'])
        self.assertIsNotNone(response.context['locations'])
        self.assertIsNone(response.context['selected_location'])
        self.assertIsNotNone(response.context['months_choices'])
        self.assertIsNotNone(response.context['years_choices'])


    def test_get_investigators(self):
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="inv1", location=uganda, backend = Backend.objects.create(name='something'))
        investigator_duplicate = Investigator.objects.create(name="inv2", mobile_number="123456789", backend = Backend.objects.create(name='something1'))
        response = self.client.get('/households/investigators?location='+str(uganda.id))
        self.failUnlessEqual(response.status_code, 200)
        result_investigator = json.loads(response.content)
        self.failUnlessEqual(result_investigator, {
            'inv1': investigator.id,
        })

    def test_get_investigators_returns_investigators_with_no_location_if_location_empty(self):
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="inv1", location=uganda, backend = Backend.objects.create(name='something'))
        investigator_duplicate = Investigator.objects.create(name="inv2", mobile_number="123456789", backend = Backend.objects.create(name='something2'))
        response = self.client.get('/households/investigators?locations=')
        self.failUnlessEqual(response.status_code, 200)
        result_investigator = json.loads(response.content)
        self.failUnlessEqual(result_investigator, {
            'inv2': investigator_duplicate.id,
        })

    def test_get_investigators_failures(self):
        response = self.client.get('/households/investigators')
        self.failUnlessEqual(response.status_code, 200)
        result_investigator = json.loads(response.content)
        self.failUnlessEqual(result_investigator, {})

    def test_validate_investigators(self):
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="inv", mobile_number='987654321', location=uganda, backend = Backend.objects.create(name='something'))
        householdForm = HouseholdForm()
        posted_locations=[uganda]
        request = MagicMock()
        request.POST={'investigator':investigator.id}

        investigator_result, investigator_form = validate_investigator(request, householdForm, posted_locations)

        self.assertEquals(investigator_result, investigator)
        self.assertEquals(investigator_form['value'],investigator.id)
        self.assertEquals(investigator_form['text'], 'inv')
        self.assertEquals(investigator_form['error'], '')
        self.assertEquals(len(investigator_form['options']),1)
        self.assertEquals(investigator_form['options'][0], investigator)

    @patch('django.forms.util.ErrorList')
    @patch('survey.models.Investigator.objects.get')
    def test_validate_investigators_no_investigator_posted(self, mock_investigator_get, mock_error_class):
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="inv", mobile_number='987654321', location=uganda, backend = Backend.objects.create(name='something'))
        householdForm = HouseholdForm()
        posted_locations=[uganda]
        request = MagicMock()
        request.POST={'investigator':investigator.id}
        mock_investigator_get.side_effect = MultiValueDictKeyError

        investigator_result, investigator_form = validate_investigator(request, householdForm, posted_locations)

        self.assertEquals(investigator_result, None)
        self.assertEquals(investigator_form['value'],'')
        self.assertEquals(investigator_form['text'], '')
        message = "No investigator provided."
        self.assertEquals(investigator_form['error'], message)
        self.assertEquals(len(investigator_form['options']),1)
        self.assertEquals(investigator_form['options'][0], investigator)
        assert mock_error_class.called_once_with([message])

    @patch('django.forms.util.ErrorList')
    @patch('survey.models.Investigator.objects.get')
    def test_validate_investigators_non_existing_investigator_id_posted(self, mock_investigator_get, mock_error_class):
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="inv", mobile_number='987654321', location=uganda, backend = Backend.objects.create(name='something'))
        householdForm = HouseholdForm()
        posted_locations=[uganda]
        request = MagicMock()
        request.POST={'investigator':'mocked so not important'}
        mock_investigator_get.side_effect = ObjectDoesNotExist

        investigator_result, investigator_form = validate_investigator(request, householdForm, posted_locations)

        self.assertEquals(investigator_result, None)
        self.assertEquals(investigator_form['value'],'mocked so not important')
        self.assertEquals(investigator_form['text'], 'mocked so not important')
        message = "You provided an unregistered investigator."
        self.assertEquals(investigator_form['error'], message)
        self.assertEquals(len(investigator_form['options']),1)
        self.assertEquals(investigator_form['options'][0], investigator)
        assert mock_error_class.called_once_with([message])

    @patch('django.forms.util.ErrorList')
    @patch('survey.models.Investigator.objects.get')
    def test_validate_investigators_NAN_investigator_id_posted(self, mock_investigator_get, mock_error_class):
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="inv", mobile_number='987654321', location=uganda, backend = Backend.objects.create(name='something'))
        householdForm = HouseholdForm()
        posted_locations=[uganda]
        request = MagicMock()
        request.POST={'investigator':'mocked so not important'}
        mock_investigator_get.side_effect = ValueError

        investigator_result, investigator_form = validate_investigator(request, householdForm, posted_locations)

        self.assertEquals(investigator_result, None)
        self.assertEquals(investigator_form['value'],'mocked so not important')
        self.assertEquals(investigator_form['text'], 'mocked so not important')
        message = "You provided an unregistered investigator."
        self.assertEquals(investigator_form['error'], message)
        self.assertEquals(len(investigator_form['options']),1)
        self.assertEquals(investigator_form['options'][0], investigator)
        assert mock_error_class.called_once_with([message])

    def test_create_households(self):
        country = LocationType.objects.create(name='country', slug='country')
        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv", mobile_number='987654321', location=uganda, backend = Backend.objects.create(name='something'))
        form_data = {
            'location': uganda.id,
            'investigator':investigator.id,
            'surname': 'Rajini',
            'first_name':'Kant',
            'male': 'False',
            'age': '20',
            'occupation':'Student',
            'level_of_education': 'Nursery',
            'resident_since_year':'2013',
            'resident_since_month':'5',
            'time_measure' : 'Years',
            'number_of_males': '2',
            'number_of_females': '3',
            'size':'5',
            'has_children':'True',
            'has_children_below_5':'True',
            'aged_between_5_12_years':'0',
            'aged_between_13_17_years':'1',
            'aged_between_0_5_months':'0',
            'aged_between_6_11_months':'0',
            'aged_between_12_23_months':'0',
            'aged_between_24_59_months':'0',
            'total_below_5':'0',
            'has_women':'True',
            'aged_between_15_19_years':'0',
            'aged_between_20_49_years':'1'
        }
        hHead = HouseholdHead.objects.filter(surname=form_data['surname'])
        household = Household.objects.filter(number_of_males=form_data['number_of_males'])
        children = Children.objects.filter(aged_between_13_17_years=form_data['aged_between_13_17_years'])
        women = Women.objects.filter(aged_between_15_19_years=form_data['aged_between_15_19_years'])
        self.failIf(hHead)
        self.failIf(household)
        self.failIf(children)
        self.failIf(women)
        response = self.client.post('/households/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 302) # ensure redirection to list investigator page

        hHead = HouseholdHead.objects.get(surname=form_data['surname'])
        household = Household.objects.get(number_of_males=form_data['number_of_males'])
        children = Children.objects.get(aged_between_13_17_years=form_data['aged_between_13_17_years'])
        women = Women.objects.get(aged_between_15_19_years=form_data['aged_between_15_19_years'])
        self.failUnless(hHead.id)
        self.failUnless(household.id)
        self.failUnless(children.id)
        self.failUnless(women.id)
        for key in ['surname', 'first_name', 'age', 'occupation',
                    'level_of_education', 'resident_since_year', 'resident_since_month']:
            value = getattr(hHead, key)
            self.assertEqual(form_data[key], str(value))

        for key in ['number_of_males', 'number_of_females']:
            value = getattr(household, key)
            self.assertEqual(form_data[key], str(value))

        for key in ['aged_between_5_12_years', 'aged_between_13_17_years', 'aged_between_0_5_months',
                    'aged_between_6_11_months', 'aged_between_12_23_months', 'aged_between_24_59_months']:
            value = getattr(children, key)
            self.assertEqual(form_data[key], str(value))

        for key in ['aged_between_15_19_years', 'aged_between_20_49_years']:
            value = getattr(women, key)
            self.assertEqual(form_data[key], str(value))

        self.assertEqual(hHead.male, False)
        self.assertEqual(household.investigator, investigator)
        self.assertEqual(hHead.household, household)
        self.assertEqual(children.household, household)
        self.assertEqual(women.household, household)

    def test_create_households_unsuccessful(self):

        country = LocationType.objects.create(name='country', slug='country')
        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv", mobile_number='987654321', location=uganda, backend = Backend.objects.create(name='something'))
        form_data = {
            'location': uganda.id,
            'investigator':investigator.id,
            'surname': 'Rajini',
            'first_name':'Kant',
            'male': 'False',
            'age': '20',
            'occupation':'Student',
            'level_of_education': 'Nursery',
            'resident_since_year':'2013',
            'resident_since_month':'5',
            'time_measure' : 'Years',
            'number_of_males': '2',
            'number_of_females': '3',
            'size':'5',
            'has_children':'True',
            'has_children_below_5':'True',
            'aged_between_5_12_years':'0',
            'aged_between_13_17_years':'1',
            'aged_between_0_5_months':'0',
            'aged_between_6_11_months':'0',
            'aged_between_12_23_months':'0',
            'aged_between_24_59_months':'0',
            'total_below_5':'0',
            'has_women':'True',
            'aged_between_15_19_years':'0',
            'aged_between_20_49_years':'1'
        }
        hHead = HouseholdHead.objects.filter(surname=form_data['surname'])
        household = Household.objects.filter(number_of_males=form_data['number_of_males'])
        children = Children.objects.filter(aged_between_13_17_years=form_data['aged_between_13_17_years'])
        women = Women.objects.filter(aged_between_15_19_years=form_data['aged_between_15_19_years'])
        self.failIf(hHead)
        self.failIf(household)
        self.failIf(children)
        self.failIf(women)

        form_with_invalid_data= form_data
        form_with_invalid_data['has_children'] = False

        response = self.client.post('/households/new/', data=form_with_invalid_data)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(response.context['selected_location'], uganda)

        hHead = HouseholdHead.objects.filter(surname=form_data['surname'])
        household = Household.objects.filter(number_of_males=form_data['number_of_males'])
        children = Children.objects.filter(aged_between_13_17_years=form_data['aged_between_13_17_years'])
        women = Women.objects.filter(aged_between_15_19_years=form_data['aged_between_15_19_years'])
        self.failIf(hHead)
        self.failIf(household)
        self.failIf(children)
        self.failIf(women)

    def assert_restricted_permission_for(self, url):
        self.client.logout()

        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)

        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%url, status_code=302, target_status_code=200, msg_prefix='')

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/households/new/')

    def test_listing_households(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda",type=country)
        investigator = Investigator.objects.create(name="inv", mobile_number='987654321', location=uganda, backend = Backend.objects.create(name='something'))
        household_a = Household.objects.create(number_of_males=1, number_of_females=2, investigator=investigator)
        household_b = Household.objects.create(number_of_males=1, number_of_females=2, investigator=investigator)
        household_c = Household.objects.create(number_of_males=1, number_of_females=2, investigator=investigator)

        HouseholdHead.objects.create(surname='Bravo', household=household_b)
        HouseholdHead.objects.create(surname='Alpha', household=household_a)
        HouseholdHead.objects.create(surname='Charlie', household=household_c)
        response = self.client.get('/households/')

        self.assertEqual(response.status_code, 200)

        templates = [template.name for template in response.templates]

        self.assertIn('households/index.html', templates)
        self.assertEqual(len(response.context['households']), 3)
        self.assertIn(household_b, response.context['households'])
        self.assertEqual(household_a, response.context['households'][0])
        self.assertEqual(household_b, response.context['households'][1])
        self.assertEqual(household_c, response.context['households'][2])

        locations = response.context['location_data'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)


    @patch('django.contrib.messages.error')
    def test_listing_no_households(self, mock_error_message):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda",type=country)
        investigator = Investigator.objects.create(name="inv", mobile_number='987654321', location=uganda, backend = Backend.objects.create(name='something'))
        Household.objects.filter(investigator=investigator).delete()
        response = self.client.get('/households/')
        self.assertEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('households/index.html', templates)

        self.assertEqual(len(response.context['households']), 0)

        locations = response.context['location_data'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

    def test_filter_list_investigators(self):
        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        county = LocationType.objects.create(name="County", slug=slugify("county"))

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=uganda, backend = Backend.objects.create(name='something1'))
        investigator2 = Investigator.objects.create(name="Investigator", mobile_number="987654322", location=kampala, backend = Backend.objects.create(name='something2'))
        investigator3 = Investigator.objects.create(name="Investigator", mobile_number="987654323", location=bukoto, backend = Backend.objects.create(name='something3'))

        household1 = Household.objects.create(investigator=investigator1)
        household2 = Household.objects.create(investigator=investigator2)
        household3 = Household.objects.create(investigator=investigator3)

        response = self.client.get("/households/?location=" + str(uganda.id))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('households/index.html', templates)

        self.assertEqual(len(response.context['households']), 3)
        for household in [household1, household2, household3]:
            self.assertIn(household, response.context['households'])

        locations = response.context['location_data'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

        self.assertEquals(len(locations['district']), 1)
        self.assertEquals(locations['district'][0], kampala)

    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/households/')

    def test_sets_location_to_household(self):
        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        county = LocationType.objects.create(name="County", slug=slugify("county"))
        sub_county = LocationType.objects.create(name="Subcounty", slug=slugify("sub-county"))
        parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
        village = LocationType.objects.create(name="Village", slug=slugify("village"))

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala_district = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto_county = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala_district)
        some_sub_county = Location.objects.create(name="Some sub county", type=sub_county, tree_parent=bukoto_county)
        some_parish = Location.objects.create(name="Some parish", type=parish, tree_parent=some_sub_county)
        some_village = Location.objects.create(name="Some village", type=village, tree_parent=some_parish)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1)
        HouseholdHead.objects.create(surname='Bravo', household=household1)
        household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county', 'Parish': 'Some parish', 'Village': 'Some village'}

        response = self.client.get('/households/')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(household_location, response.context['households'][0].related_locations)

