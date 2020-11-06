from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

# Create your tests here.

from .models import userAccount, Course, buddies

def create_user(user, name, major, bio):
    """
    creates a userAccount with the given user and name arguments
    """
    return userAccount.objects.create(user=user,name=name, major=major, bio=bio)


def create_course(student, mnemonic, number):
    """
    creates a userAccount with the given user and name arguments
    """
    return Course.objects.create(student=student,mnemonic=mnemonic, number=number)

def create_buddy(requester, requestee, approved):
    """
    creates a buddy relation with the given requester and requestee and approved value
    """
    return buddies.objects.create(requester=requester, requestee=requestee, request_message="", approved=approved, denied_message="", denied=False)

class userAccountModelTest(TestCase):
    def test_self_str(self):
        """
        userAccount returns name property
        """
        testUser = User.objects.create_user(username="testUser", password="testPassword")
        testAccount = userAccount(user=testUser, name="John Doe")
        self.assertEqual(str(testAccount),"John Doe")
    def test_getCourses(self):
        """
        userAccount getCourses return list of associated courses
        """
        testUser = User.objects.create_user(username="testUser", password="testPassword")
        testAccount = create_user(user=testUser, name="John Doe", major="CS", bio="sample")
        create_course(testAccount, "CS", "3240")
        create_course(testAccount, "MATH", "1010")
        self.assertEqual(list(testAccount.getCourses()), list(Course.objects.all()))
        
    def test_getBuddies_accepted(self):
        """
        userAccount get buddies returns the accepted buddies
        """
        testUser = User.objects.create_user(username="testUser", password="testPassword")
        testRequestee = User.objects.create_user(username="testRequestee", password="testPassword")
        testAccount = create_user(user=testUser, name="John Doe", major="CS", bio="sample")
        testRequesteeAccount = create_user(user=testRequestee, name="John Doe", major="CS", bio="sample")
        create_buddy(testAccount,testRequesteeAccount, True)
        self.assertEqual(testAccount.getBuddies()["accepted"][0],testRequesteeAccount)
    
    def test_getBuddies_their_approval(self):
        """
        userAccount get buddies returns the waiting for their approval buddies
        """
        testUser = User.objects.create_user(username="testUser", password="testPassword")
        testRequestee = User.objects.create_user(username="testRequestee", password="testPassword")
        testAccount = create_user(user=testUser, name="John Doe", major="CS", bio="sample")
        testRequesteeAccount = create_user(user=testRequestee, name="John Doe", major="CS", bio="sample")
        create_buddy(testAccount,testRequesteeAccount, False)
        self.assertEqual(testAccount.getBuddies()["pendingTheirApproval"][0],testRequesteeAccount)

    def test_getBuddies_your_approval(self):
        """
        userAccount get buddies returns the waiting for your approval buddies
        """
        testUser = User.objects.create_user(username="testUser", password="testPassword")
        testRequester = User.objects.create_user(username="testRequester", password="testPassword")
        testAccount = create_user(user=testUser, name="John Doe", major="CS", bio="sample")
        testRequesterAccount = create_user(user=testRequester, name="John Doe", major="CS", bio="sample")
        create_buddy(testRequesterAccount,testAccount, False)
        self.assertEqual(testAccount.getBuddies()["pendingYourApproval"][0],testRequesterAccount)
    
    def test_getSharedCourses(self):
        """
        userAccount get sharedCourses returns list of shared courses
        """
        testUser = User.objects.create_user(username="testUser", password="testPassword")
        testUser2 = User.objects.create_user(username="testUser2", password="testPassword")
        testAccount = create_user(user=testUser, name="John Doe", major="CS", bio="sample")
        testAccount2 = create_user(user=testUser2, name="John Doe", major="CS", bio="sample")
        shared = create_course(testAccount, "CS", "3240")
        create_course(testAccount, "MATH", "1010")
        create_course(testAccount2, "CS", "3240")
        create_course(testAccount2, "STS", "4500")
        self.assertEqual(testAccount.getSharedCourses(testAccount2),[shared])


class userAccountHasAccountViewTests(TestCase):
    def test_logged_in(self):
        """
        logged in users get redirected to account page
        """
        testUser = User.objects.create_user(username="testUser", password="testPassword")
        login = self.client.force_login(testUser)
        url = reverse('userAccount:has_account')
        response = self.client.get(url)
        self.assertRedirects(response, '/profile/')

class userAccountViewAccountViewTests(TestCase):
    def test_view_account(self):
        """
        user's name shows up in response when account is already set up
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        url = reverse('userAccount:has_account')
        response = self.client.get(url, follow=True)
        self.assertContains(response, "John Doe")

class userAccountSaveViewTests(TestCase):
    def test_name_update_account(self):
        """
        name updates when saved
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        uA = create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        url = reverse('userAccount:save')
        data = {
            'acc_name' : 'James',
            'acc_major' : '',
            'acc_bio' : '',
        }
        self.client.post(url,data)
        response = self.client.get(reverse('userAccount:view_account'))
        self.assertContains(response, "James")

    def test_major_update_account(self):
        """
        major updates when saved
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        url = reverse('userAccount:save')
        data = {
            'acc_name' : 'John Doe',
            'acc_major' : 'Psychology',
            'acc_bio' : '',
        }
        self.client.post(url,data)
        response = self.client.get(reverse('userAccount:view_account'))
        self.assertContains(response, "Psychology")

    def test_bio_update_account(self):
        """
        bio updates when saved
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        url = reverse('userAccount:save')
        data = {
            'acc_name' : 'John Doe',
            'acc_major' : '',
            'acc_bio' : 'Hello I am John Doe',
        }
        self.client.post(url,data)
        response = self.client.get(reverse('userAccount:view_account'))
        self.assertContains(response, "Hello I am John Doe")

class CourseModelTests(TestCase):
    def test_self_str(self):
        """
        Course returns mnemonicnumber for name
        """
        testUser = User.objects.create_user(username="testUser", password="testPassword")
        testAccount = userAccount(user=testUser, name="John Doe")
        testCourse = Course(student=testAccount, mnemonic="CS", number = "3240")
        self.assertEqual(str(testCourse),"CS3240 for John Doe")
    def test_equals(self):
        testUser = User.objects.create_user(username="testUser", password="testPassword")
        testUser2 = User.objects.create_user(username="testUser2", password="testPassword")
        testAccount = create_user(user=testUser, name="John", major="CS", bio="sample")
        testAccount2 = create_user(user=testUser2, name="Doe", major="CS", bio="sample")
        course1 = create_course(testAccount, "CS", "3240")
        course2 = create_course(testAccount2, "CS", "3240")
        self.assertEqual(course1, course2)


class userAccountCourseViewTests(TestCase):
    def test_course_list(self):
        """
        account view should show list of courses associated with student acount
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        testAccount = userAccount.objects.all()[0]
        create_course(student=testAccount, mnemonic="CS", number="3240")
        url = reverse('userAccount:view_account')
        response = self.client.get(url, follow=True)
        self.assertContains(response, "CS3240")

    def test_no_course_list(self):
        """
        account view with no courses should say so
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        url = reverse('userAccount:view_account')
        response = self.client.get(url, follow=True)
        self.assertContains(response, "No courses have been added to the account")

class userAccountCourseManipulationTests(TestCase):
    def test_add_course(self):
        """
        adding a course appends to account profile view
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        url = reverse('userAccount:add_course')
        data = {'course_mnemonic' : 'CS', 'course_number' : '1010'}
        self.client.post(url,data)
        response = self.client.get(reverse('userAccount:view_account'))
        self.assertContains(response,"CS1010")

    def test_add_invalid_course(self):
        """
        adding an invalid course will report an error message
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        url = reverse('userAccount:add_course')
        data = {'course_mnemonic' : 'CSFFF', 'course_number' : '2'}
        self.client.post(url,data)
        response = self.client.get(reverse('userAccount:view_account'))
        self.assertContains(response,"Incorrect course format")

    def test_delete_course(self):
        """
        deleting a course removes it from account view
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        testAccount = userAccount.objects.all()[0]
        create_course(student=testAccount, mnemonic="CS", number="3240")
        pk = Course.objects.all()[0].pk
        url = reverse('userAccount:delete_course')
        data = {'delete_item' : [pk]}
        self.client.post(url,data)
        url = reverse('userAccount:view_account')
        response = self.client.get(url, follow=True)
        self.assertContains(response, "No courses have been added to the account")

class userAccountBuddyViewTests(TestCase):
    def test_add_course(self):
        """
        adding a course appends to account profile view
        """
        testUser = User.objects.create_user(username="testUser", email = "email@virginia.edu", password="testPassword")
        create_user(user=testUser, name="John Doe", major='', bio='')
        login = self.client.force_login(testUser)
        url = reverse('userAccount:add_course')
        data = {'course_mnemonic' : 'CS', 'course_number' : '1010'}
        self.client.post(url,data)
        response = self.client.get(reverse('userAccount:view_account'))
        self.assertContains(response,"CS1010")