##Explore uSurvey

###Roles in uSurvey: 

1.	Admin: Creates uSurvey Users and assigns them Roles
2.	Data Researcher: Creates and defines Modules, Groups, Listing, Survey and Questions. Also defines interviewers and assigns them to an Enumeration area to conduct survey 
3.	Interviewer: Conducts the actual survey on the field in designated enumeration area
 

###Module: 
Is a high level classification of surveys, based upon subject, surveys are classified.
Ex: Household survey, School survey, etc

<b>Purpose</b>: Identity of a Survey.

<b>Precondition</b>: No dependency, can be created independently.


###Groups: 
It is the categorization of people/ respondents with in a Survey.
Ex: Men, Women, Boys with age less than 18 years, etc

<b>Purpose</b>: To differentiate the people/ respondents , to apply logic and to set Questions.

<b>Precondition</b>: No dependency, can be created independently.

 
###Listing:  
It is the set of questions, each question is assigned to variable and these listings can be configurable/ reusable for any of the surveys.

<b>Purpose</b>: Reusability, looping of set Questions.

<b>Precondition</b>: No dependency, can be created independently.

###Create a Survey: 
A new survey can be created and defined here, one has to provide Name, Description, survey type (Sampled or Census) and sample size of the survey and options like  preferred listing, Groups are selected.

<b>Purpose</b>: to conduct a survey.

<b>Precondition</b>: dependency on Groups, Listing.


###New Interviewer: 
Interviewer registration is done, Token Name and Id are given and assigned to a Module and enumeration area to conduct survey.

<b>Purpose</b>: to conduct a survey.

<b>Precondition</b>:  dependency on Survey, enumeration area.



###Groups:

Grouping is available from main menu under <b>Survey Administration</b> >> <b>Groups</b>

Groups are Survey dependent classification of people/respondents into one or more Groups.
Each group contains set of Variables, every Question is assigned to an identifier called ‘Variable’
   
 ![uSurvey map page](https://github.com/madhavaramu/uSurvey/blob/uSurvey/screenshots/Map_groupZ_selected.png)

###Creating Groups:

Navigate to <b>Survey Administration</b> >> <b>Groups</b>

 ![Create Groups](https://github.com/madhavaramu/uSurvey/blob/uSurvey/screenshots/Add_Groups.png)
 
The above Groups page is used to manage Groups, i.e. to Create a New Group, Edit existing Group, Delete Groups and Manage Variables.

###Manage Variables:

 click on ‘Manage Variables’ button to view list of existing Variables and options to Add, Edit and Delete Variables
 
 ![Manage Variables](https://github.com/madhavaramu/uSurvey/blob/uSurvey/screenshots/addvariable.png)
 
###Add Variables:
 
 click on 'Add Variables' button, to navigare below show form. Where one can create new variable by assigning question. Provide 'variable Name' and Question in 'Text' feilds and select 'Answer' type.  
 
 ![Add Variables](https://github.com/madhavaramu/uSurvey/blob/uSurvey/screenshots/Add_Variable.png)
 
 
###Edit Group:
 
 To Edit existing Group, every corresponding Group name has Actions column with Action items ‘Edit’ and ‘Delete’, select Edit to modify the Group.
 
 ![Edit Groups](https://github.com/madhavaramu/uSurvey/blob/uSurvey/screenshots/Edit_group.png)

