from django.test.client import Client
from django.contrib.auth.models import User
from rapidsms.contrib.locations.models import Location, LocationType
from survey.investigator_configs import PRIME_LOCATION_TYPE
from survey.models import HouseholdMemberGroup
from survey.models.surveys import Survey
from survey.models.question import Question
from survey.models.batch import Batch
from survey.tests.base_test import BaseTest
from survey.forms.batch import BatchForm, BatchQuestionsForm


class BatchViews(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_batches')
        raj = self.assign_permission_to(raj, 'can_view_investigators')

        self.client.login(username='Rajni', password='I_Rock')
        self.survey = Survey.objects.create(name='survey name', description= 'survey descrpition', type=False, sample_size=10)
        self.batch = Batch.objects.create(order = 1, name = "Batch A",survey=self.survey)
        district = LocationType.objects.create(name=PRIME_LOCATION_TYPE, slug=PRIME_LOCATION_TYPE)
        self.kampala = Location.objects.create(name="Kampala", type=district)
        city = LocationType.objects.create(name="City", slug="city")
        village = LocationType.objects.create(name="Village", slug="village")
        self.kampala_city = Location.objects.create(name="Kampala City", type=city, tree_parent=self.kampala)
        self.bukoto = Location.objects.create(name="Bukoto", type=city, tree_parent=self.kampala)
        self.kamoja = Location.objects.create(name="kamoja", type=village, tree_parent=self.bukoto)
        self.abim = Location.objects.create(name="Abim", type=district)
        self.batch.open_for_location(self.abim)

    def test_get_index(self):
        response = self.client.get('/surveys/%d/batches/' %self.survey.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/index.html', templates)
        self.assertIn(self.batch, response.context['batches'])
        self.assertEquals(self.survey, response.context['survey'])

    def test_get_index_should_not_show_batches_not_belonging_to_the_survey(self):
        another_batch = Batch.objects.create(order = 2, name = "Batch B")
        response = self.client.get('/surveys/%d/batches/' %self.survey.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/index.html', templates)
        self.assertIn(self.batch, response.context['batches'])
        self.assertFalse(another_batch in response.context['batches'])
        self.assertEquals(self.survey, response.context['survey'])

    def test_get_batch_view(self):
        response = self.client.get('/surveys/%d/batches/%d/' %(self.survey.id, self.batch.pk))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/show.html', templates)
        self.assertEquals(self.batch, response.context['batch'])
        self.assertIn(self.kampala, response.context['locations'])
        self.assertIn(self.abim, response.context['open_locations'])

    def test_open_batch_for_location(self):
        self.assertFalse(self.batch.is_open_for(self.kampala))
        response = self.client.post('/batches/' + str(self.batch.pk) + "/open_to", data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertTrue(self.batch.is_open_for(loc))

    def test_close_batch_for_location(self):
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.batch.open_for_location(loc)

        response = self.client.post('/batches/' + str(self.batch.pk) + "/close_to", data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertFalse(self.batch.is_open_for(loc))


    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/surveys/%d/batches/' %self.survey.id)
        self.assert_restricted_permission_for('/surveys/%d/batches/new/'%self.survey.id)
        self.assert_restricted_permission_for('/surveys/%d/batches/1/'%self.survey.id)
        self.assert_restricted_permission_for('/batches/1/open_to')
        self.assert_restricted_permission_for('/batches/1/close_to')
        self.assert_restricted_permission_for('/surveys/%d/batches/%d/edit/'%(self.survey.id, self.batch.id))

    def test_add_new_batch_should_load_new_template(self):
        response = self.client.get('/surveys/%d/batches/new/'%self.survey.id)
        self.assertEqual(response.status_code,200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/new.html', templates)

    def test_batch_form_is_in_response_request_context(self):
        response = self.client.get('/surveys/%d/batches/new/'%self.survey.id)
        self.assertIsInstance(response.context['batchform'], BatchForm)
        self.assertEqual(response.context['button_label'], 'Save')
        self.assertEqual(response.context['id'], 'add-batch-form')

    def test_post_add_new_batch_is_invalid_if_name_field_is_empty(self):
        response = self.client.post('/surveys/%d/batches/new/'%self.survey.id, data={'name':'', 'description':''})
        self.assertTrue(len(response.context['batchform'].errors)>0)

    def test_post_add_new_batch(self):
        response = self.client.post('/surveys/%d/batches/new/'%self.survey.id, data={'name':'Batch1', 'description':'description'})
        self.assertEqual(len(Batch.objects.filter(name='Batch1')),1)

    def test_post_add_new_batch_redirects_to_batches_table_if_valid(self):
         response = self.client.post('/surveys/%d/batches/new/'%self.survey.id, data={'name':'Batch1', 'description':'description'})
         self.assertRedirects(response, expected_url='/surveys/%d/batches/' %self.survey.id, status_code=302, target_status_code=200, msg_prefix='')

    def test_post_should_not_add_batch_with_existing_name(self):
        response = self.client.post('/surveys/%d/batches/new/'%self.survey.id, data={'name':'Batch A', 'description':'description'})
        self.assertTrue(len(response.context['batchform'].errors)>0)

    def post_add_new_batch_should_add_batch_to_the_survey(self):
        form_data = {'name': 'Some Batch', 'description': 'some description'}
        self.failIf(Batch.objects.filter(**form_data))
        response = self.client.post('/surveys/%d/batches/new/'%self.survey.id, data=form_data)
        batch = Batch.objects.get(**form_data)
        self.assertEqual(self.survey,batch.survey)

    def test_edit_batch_should_load_new_template(self):
        batch = Batch.objects.create(name="batch a", description="batch a description")
        response = self.client.get('/surveys/%d/batches/%d/edit/'%(self.survey.id, self.batch.id))
        self.assertEqual(response.status_code,200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/new.html', templates)

    def test_edit_batch_page_gets_batch_form_instance(self):
        batch = Batch.objects.create(name="batch a", description="batch a description")
        response = self.client.get('/surveys/%d/batches/%d/edit/'%(self.survey.id, batch.id))
        self.assertIsInstance(response.context['batchform'], BatchForm)
        self.assertEqual(response.context['batchform'].initial['name'], batch.name)
        self.assertEqual(response.context['button_label'], 'Save')
        self.assertEqual(response.context['id'], 'add-batch-form')

    def test_save_edited_batch(self):
        batch = Batch.objects.create(name="batch a", description="batch a description")
        form_data={
                    'name': 'batch aaa',
                    'description': batch.description
        }
        response = self.client.post('/surveys/%d/batches/%d/edit/'%(self.survey.id, batch.id),data=form_data)
        updated_batch = Batch.objects.get(name=form_data['name'])
        self.failUnless(updated_batch)
        self.failIf(Batch.objects.filter(name=batch.name))
        self.assertRedirects(response, expected_url='/surveys/%d/batches/' %self.survey.id, status_code=302, target_status_code=200, msg_prefix='')

    def test_delete_batch(self):
        response = self.client.get('/surveys/%d/batches/%d/delete/'%(self.survey.id, self.batch.id))
        recovered_batch = Batch.objects.filter(id=self.batch.id)
        self.assertRedirects(response, expected_url='/surveys/%d/batches/' %self.survey.id, status_code=302, target_status_code=200, msg_prefix='')
        self.failIf(recovered_batch)

    def test_assign_question_to_the_batch_should_show_list_of_questions(self):
        group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        response = self.client.get('/batches/%d/assign_questions/'%(self.batch.id))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/assign.html', templates)

        question = Question.objects.create(group=group, text="Haha?")
        self.assertEqual(1, len(response.context['batch_questions_form'].fields['questions']._queryset))
        self.assertIn(question, response.context['batch_questions_form'].fields['questions']._queryset)
        self.assertEqual(self.batch, response.context['batch'])
        self.assertIsInstance(response.context['batch_questions_form'],BatchQuestionsForm)
        self.assertEqual(response.context['button_label'], 'Save')
        self.assertEqual(response.context['id'], 'assign-question-to-batch-form')
        self.assertEqual(1, len(response.context['groups']))
        self.assertIn(group, response.context['groups'])

    def test_post_assign_questions_to_batch_should_save_questions(self):
        q1=Question.objects.create(text="question1", answer_type=Question.NUMBER)
        q2=Question.objects.create(text="question2", answer_type=Question.TEXT)
        form_data = {
                    'questions': [q1.id, q2.id],
                }
        self.failIf(self.batch.all_questions())
        response = self.client.post('/batches/%d/assign_questions/'%(self.batch.id),data=form_data)
        self.assertRedirects(response, expected_url='batches/%d/questions/' %self.batch.id, status_code=302, target_status_code=200, msg_prefix='')
        self.assertEqual(2, len(self.batch.all_questions()))
        self.assertIn(q1, self.batch.all_questions())
        self.assertIn(q2, self.batch.all_questions())
        success_message ="Questions successfully assigned to batch: %s."%self.batch.name.capitalize()
        self.assertTrue(success_message in response.cookies['messages'].value)

