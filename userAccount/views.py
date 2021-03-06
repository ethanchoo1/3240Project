from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .models import userAccount, Course, Availability, buddies, Message, ZoomMeeting
from django.template import loader
from django.contrib import messages
from django.contrib.auth.models import User
from .const_data import major_options, course_data, dummy_convo
import random
import json
import requests
from zoomus import ZoomClient
import datetime
from .forms import MyForm


# Create your views here.

def has_availability(request):
    if (request.user.is_authenticated):
        if (userAccount.objects.filter(user=request.user).count() > 0):
            return HttpResponseRedirect(reverse('userAccount:view_availability'))
        else:
            user = request.user
            new_account = userAccount(user=user, first_name="", last_name="")
            new_account.save()
            return HttpResponseRedirect(reverse('userAccount:view_availability'))
    else:
        messages.add_message(request, messages.ERROR, "Login before attempting to view availability")
        return HttpResponseRedirect(reverse('login:login'))

def view_availability(request):
    if (request.user.is_authenticated):
        currentUser = userAccount.objects.get(user=request.user)
        availability = currentUser.availability.all()
        calendar = ""
        if availability.count() > 0:
            calendar = availability[0].calendar

        template = loader.get_template('userAccount/availabilityForm.html')
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        times = []
        for i in range(8, 12):
            times.append(str(i) + ":00 AM")
        times.append("12:00 PM")
        for i in range(1,12):
            times.append(str(i) + ":00 PM")

        context = {
            'range16': range(16),
            'range7': range(7),
            'days': days,
            'times': times,
            'calendar': calendar
            }
        return HttpResponse(template.render(context, request))
    else:
        messages.add_message(request, messages.ERROR, "Login before attempting to view availability")
        return HttpResponseRedirect(reverse('login:login'))

def save_availability(request):
    try:
        student = userAccount.objects.get(user=request.user)
        old_availability = student.availability.all()
        if old_availability.count() > 0:
            old_availability[0].delete()
            
        calendar = request.POST.get("calendar")

        availability = Availability(student=student, calendar=calendar)
        availability.save()
        messages.add_message(request, messages.SUCCESS, "Account information successfully updated")
        return HttpResponseRedirect(reverse('userAccount:view_availability'))
    except:
        if(request.user.is_authenticated):
            messages.add_message(request, messages.ERROR, "Error updating account information")
            return HttpResponseRedirect(reverse('userAccount:view_account'))
        else:
            messages.add_message(request, messages.ERROR, "Login before attempting to view account")
            return HttpResponseRedirect(reverse('login:login'))
    
def has_account(request):
    if(request.user.is_authenticated):
        if(userAccount.objects.filter(user=request.user).count()>0):
            return HttpResponseRedirect(reverse('userAccount:view_account'))
        else:
            user = request.user
            new_account = userAccount(user=user, first_name=user.first_name, last_name=user.last_name)
            new_account.save()
            return HttpResponseRedirect(reverse('userAccount:view_account'))
    else:
        messages.add_message(request, messages.ERROR, "Login before attempting to view account")
        return HttpResponseRedirect(reverse('login:login'))

def view_account(request):
    if(request.user.is_authenticated):
        template = loader.get_template('userAccount/accountForm.html')
        currentUser = userAccount.objects.get(user=request.user)
        courses = currentUser.getCourses()

        courses_as_str = []
        for course in courses:
            courses_as_str.append(course.mnemonic + " " + course.number)

        context = {
            'acc_first_name' : currentUser.first_name,
            'acc_last_name' : currentUser.last_name,
            'acc_major' : currentUser.major,
            'acc_bio' : currentUser.bio,
            'email' : currentUser.user.email,
            'courses' : ','.join(courses_as_str),
            'major_options' : major_options,
            'course_data' : course_data
        }
        return HttpResponse(template.render(context,request))
    else:
        messages.add_message(request, messages.ERROR, "Login before attempting to view account")
        return HttpResponseRedirect(reverse('login:login'))

def save(request):
    try:
        currentUser = userAccount.objects.get(user=request.user)
        acc_first_name = request.POST.get("acc_first_name")
        acc_last_name = request.POST.get("acc_last_name")
        acc_major = request.POST.get("acc_major")
        acc_bio = request.POST.get("acc_bio")
        currentUser.first_name = acc_first_name
        currentUser.last_name = acc_last_name
        currentUser.major = acc_major
        currentUser.bio = acc_bio
        currentUser.save()

        courses_to_add = request.POST.getlist("acc_courses_added[]")
        courses_to_remove = request.POST.getlist("acc_courses_removed[]")
        all_courses = Course.objects.filter(student=currentUser)

        for delete_course in courses_to_remove:
            for course in all_courses:
                if course.mnemonic == delete_course.split(" ")[0] and course.number == delete_course.split(" ")[1]:
                    course.delete()
        
        for add_course in courses_to_add:

            # Will quietly ignore any duplicate courses
            is_duplicate = False
            for course in all_courses:
                if course.mnemonic == add_course.split(" ")[0] and course.number == add_course.split(" ")[1]:
                    is_duplicate = True

            if not is_duplicate:
                new_course = Course(student=currentUser, mnemonic=add_course.split(" ")[0], number=add_course.split(" ")[1])
                new_course.save()

        messages.add_message(request, messages.SUCCESS, "Account information successfully updated")
        return HttpResponseRedirect(reverse('userAccount:contact_info'))
    except:
        if(request.user.is_authenticated):
            messages.add_message(request, messages.ERROR, "Error updating account information")
            return HttpResponseRedirect(reverse('userAccount:view_account'))
        else:
            messages.add_message(request, messages.ERROR, "Login before attempting to view account")
            return HttpResponseRedirect(reverse('login:login'))


def view_buddies(request):
    if(request.user.is_authenticated):
        if (userAccount.objects.filter(user=request.user).count() > 0):
            currentUser = userAccount.objects.get(user=request.user)
        else:
            return HttpResponseRedirect(reverse('login:home'))

        template = loader.get_template('userAccount/buddies.html')
        buddies = currentUser.getBuddies()

        buddies_with_notifications = []
        buddy_num_notifications = {}

        for buddy in buddies["accepted"]:
            num_unread = get_num_unread(buddy, request.user)
            if num_unread != 0:
                buddies_with_notifications.append(buddy.user)
                buddy_num_notifications[buddy.user] = num_unread

        for buddy in buddies["pendingYourApproval"]:
            num_unread = get_num_unread(buddy, request.user)
            if num_unread != 0:
                buddies_with_notifications.append(buddy.user)
                buddy_num_notifications[buddy.user] = num_unread

        for buddy in buddies["pendingTheirApproval"]:
            num_unread = get_num_unread(buddy, request.user)
            if num_unread != 0:
                buddies_with_notifications.append(buddy.user)
                buddy_num_notifications[buddy.user] = num_unread

        context = {
            'acc_name' : currentUser.first_name + ' ' +currentUser.last_name,
            'accepted_buddies' : buddies["accepted"],
            'pending_your_approval' : buddies["pendingYourApproval"],
            'pending_their_approval' : buddies["pendingTheirApproval"],
            'selected_buddy' : None,
            'buddies_with_notifications': buddies_with_notifications,
            'buddy_num_notifications': buddy_num_notifications
        }
        return HttpResponse(template.render(context,request))
    else:
        messages.add_message(request, messages.ERROR, "Login before attempting to view buddies")
        return HttpResponseRedirect(reverse('login:login'))

def buddy_select(request, buddy_name):
    if(request.user.is_authenticated):
        buddy = User.objects.get(username=buddy_name)
        buddy_account = userAccount.objects.get(user=buddy)
        study_buddy_list_length = len(buddy_account.getBuddies()["accepted"])
        template = loader.get_template('userAccount/buddies.html')
        currentUser = userAccount.objects.get(user=request.user)
        buddies = currentUser.getBuddies()
        shared_courses = currentUser.getSharedCourses(buddy_account)

        # Availability
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        times = []
        for i in range(8, 12):
            times.append(str(i) + ":00 AM")
        times.append("12:00 PM")
        for i in range(1,12):
            times.append(str(i) + ":00 PM")

        user_availability = Availability.objects.get(student=currentUser).calendar
        buddy_availability = Availability.objects.get(student=buddy_account).calendar

        form = MyForm()
        meeting = currentUser.getUpcomingMeetings(buddy_account)

        # Notifications
        buddies_with_notifications = []
        buddy_num_notifications = {}

        for buddy in buddies["accepted"]:
            num_unread = get_num_unread(buddy, request.user)
            if num_unread != 0:
                buddies_with_notifications.append(buddy.user)
                buddy_num_notifications[buddy.user] = num_unread

        for buddy in buddies["pendingYourApproval"]:
            num_unread = get_num_unread(buddy, request.user)
            if num_unread != 0:
                buddies_with_notifications.append(buddy.user)
                buddy_num_notifications[buddy.user] = num_unread

        for buddy in buddies["pendingTheirApproval"]:
            num_unread = get_num_unread(buddy, request.user)
            if num_unread != 0:
                buddies_with_notifications.append(buddy.user)
                buddy_num_notifications[buddy.user] = num_unread
        
        context = {
            'acc_name' : currentUser.first_name + ' ' +currentUser.last_name,
            'current_user': currentUser,
            'accepted_buddies' : buddies["accepted"],
            'pending_your_approval' : buddies["pendingYourApproval"],
            'pending_their_approval' : buddies["pendingTheirApproval"],
            'denied_buddies' : buddies["denied"], 
            'selected_buddy' : buddy_account,
            'number_buddies' : study_buddy_list_length,
            'shared_courses' : shared_courses,
            'user_availability': user_availability,
            'buddy_availability': buddy_availability,
            'range16': range(16),
            'range7': range(7),
            'days': days,
            'times': times,
            'form' : form,
            'meeting' : meeting,
            'buddies_with_notifications': buddies_with_notifications,
            'buddy_num_notifications': buddy_num_notifications
        }
        return HttpResponse(template.render(context,request))
    else:
        messages.add_message(request, messages.ERROR, "Login before attempting to view buddies")
        return HttpResponseRedirect(reverse('login:login'))  

def approve_buddy(request):
    try:
        buddy_pk = request.POST.getlist('approve_item')[0]
        buddy_to_approve = userAccount.objects.get(pk=buddy_pk)
        currentUser = userAccount.objects.get(user=request.user)
        buddyObject = buddies.objects.get(requester=buddy_to_approve, requestee=currentUser)
        buddyObject.approved = True
        buddyObject.save()
        messages.add_message(request, messages.SUCCESS, "Approval successful")
        return HttpResponseRedirect(reverse('userAccount:view_buddies'))
    except:
        if(request.user.is_authenticated):
            messages.add_message(request, messages.ERROR, "Error approving request")
            return HttpResponseRedirect(reverse('userAccount:view_buddies'))
        else:
            messages.add_message(request, messages.ERROR, "Login before attempting to view account")
            return HttpResponseRedirect(reverse('login:login'))

def deny_buddy(request):
    try:
        buddy_pk = request.POST.getlist('deny_item')[0]
        buddy_to_approve = userAccount.objects.get(pk=buddy_pk)
        currentUser = userAccount.objects.get(user=request.user)
        buddyObject = buddies.objects.get(requester=buddy_to_approve, requestee=currentUser)
        buddyObject.denied = True
        buddyObject.save()
        messages.add_message(request, messages.SUCCESS, "Approval denied")
        return HttpResponseRedirect(reverse('userAccount:view_buddies'))
    except:
        if(request.user.is_authenticated):
            messages.add_message(request, messages.ERROR, "Error denying request")
            return HttpResponseRedirect(reverse('userAccount:view_buddies'))
        else:
            messages.add_message(request, messages.ERROR, "Login before attempting to view account")
            return HttpResponseRedirect(reverse('login:login'))

def contact_info(request):
    if(request.user.is_authenticated):
        template = loader.get_template('userAccount/contactInfo.html')
        currentUser = userAccount.objects.get(user=request.user)
        context = {
            'computing_id' : currentUser.computing_id,
            'phone_number' : currentUser.phone_number,
            'discord_name' : currentUser.discord_name,
        }
        return HttpResponse(template.render(context,request))
    else:
        messages.add_message(request, messages.ERROR, "Login before attempting to edit contact info")
        return HttpResponseRedirect(reverse('login:login'))

def save_contact(request):
    try:
        currentUser = userAccount.objects.get(user=request.user)
        computing_id = request.POST.get("computing_id")
        phone_number = request.POST.get("phone_number")
        discord_name = request.POST.get("discord_name")
        currentUser.computing_id = computing_id
        currentUser.phone_number = phone_number
        currentUser.discord_name = discord_name
        currentUser.save()
        messages.add_message(request, messages.SUCCESS, "Contact information successfully updated")
        return HttpResponseRedirect(reverse('userAccount:contact_info'))
    except:
        if(request.user.is_authenticated):
            messages.add_message(request, messages.ERROR, "Error updating contact information")
            return HttpResponseRedirect(reverse('userAccount:contact_info'))
        else:
            messages.add_message(request, messages.ERROR, "Login before attempting to view contact information")
            return HttpResponseRedirect(reverse('login:login'))

def format_date(year, month, day, hour, minute, second):
    if (hour > 19):
        hour = (hour+5) % 24
        date = datetime.datetime(year, month, day, hour, minute, second)
        date += datetime.timedelta(days=1)
        return date
    else:
        return datetime.datetime(year, month, day, hour+5, minute, second)

def zoom(request):
    try:
        client = ZoomClient('3NKu1UtkSpW1FiCCrFrykg', '5qq7tR3ZBS2lJth3FgAqUasKDxP5KiYPMVPF')
        user_list_response = client.user.list()
        user_list = json.loads(user_list_response.content)
        client_id = (user_list['users'][0]['id'])
        dtime = request.POST.get("datetime_field")
        date_time = dtime.split(" ")
        date = date_time[0].split("-")
        time = date_time[1].split(":")
        zoom_date = format_date(int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]), int(time[2]))
        settings = {"host_video": True,"participant_video": True,"cn_meeting": False ,"in_meeting": False,"join_before_host": True, "mute_upon_entry": False,"watermark": False,"use_pmi": False,"approval_type": 2,"audio": "both","auto_recording": "none","alternative_hosts": "","close_registration": True,"waiting_room": False,"contact_name": "me","contact_email": "ec4kj@virginia.edu","registrants_email_notification": True,"meeting_authentication": False,"authentication_option": "","authentication_domains": ""}
        meeting = client.meeting.create(user_id=client_id, start_time=zoom_date, topic="Study Buddy Meeting", settings=settings)
        content = json.loads(meeting.content)
        link = content["join_url"]
        buddy_pk = request.POST.getlist('zoom_item')[0]
        buddy_account = userAccount.objects.get(pk=buddy_pk)
        currentUser = userAccount.objects.get(user=request.user)
        buddyObject = currentUser.getBuddyObject(buddy_account)
        meeting_object = ZoomMeeting(buddies=buddyObject, meeting_link=link, start_time=dtime)
        meeting_object.save()

        messages.add_message(request, messages.SUCCESS, "Meeting created successfully")
        src_url = request.META.get('HTTP_REFERER')
        if src_url != None:
            return redirect(src_url)
        else:
            return HttpResponseRedirect(reverse('userAccount:view_buddies'))
    except:
        if(request.user.is_authenticated):
            messages.add_message(request, messages.ERROR, "Error creating zoom meeting")
            return HttpResponseRedirect(reverse('userAccount:view_buddies'))
        else:
            messages.add_message(request, messages.ERROR, "Login before attempting to view contact information")
            return HttpResponseRedirect(reverse('login:login'))

def remove_zoom(request):
    try:
        meeting_pk = request.POST.getlist('meeting_item')[0]
        meeting_to_delete = ZoomMeeting.objects.get(pk=meeting_pk)
        meeting_to_delete.delete()
        messages.add_message(request, messages.SUCCESS, "Meeting deleted")

        src_url = request.META.get('HTTP_REFERER')
        if src_url != None:
            return redirect(src_url)
        else:
            return HttpResponseRedirect(reverse('userAccount:view_buddies'))
    except:
        if(request.user.is_authenticated):
            messages.add_message(request, messages.ERROR, "Error deleteing meeting")
            return HttpResponseRedirect(reverse('userAccount:view_buddies'))
        else:
            messages.add_message(request, messages.ERROR, "Login before attempting to view account")
            return HttpResponseRedirect(reverse('login:login'))

def get_buddy_obj(user, buddy_name):
    buddy = User.objects.get(username=buddy_name)
    buddy_acc = userAccount.objects.get(user=buddy)
    user_acc = userAccount.objects.get(user=user)

    user_is_requester = False

    buddy_query = buddies.objects.filter(requester=buddy_acc, requestee=user_acc)
    if buddy_query.count() == 0:
        buddy_query = buddies.objects.filter(requester=user_acc, requestee=buddy_acc)
        user_is_requester = True
    else:
        user_is_requester = False

    if buddy_query.count() == 0:
        return tuple()

    return (buddy_query[0], user_is_requester)

def get_num_unread(buddy, user):
    buddy_obj_tuple = get_buddy_obj(user, buddy.user)
    if len(buddy_obj_tuple) == 0:
        return 0
    
    buddy_obj = buddy_obj_tuple[0]
    user_is_requester = buddy_obj_tuple[1]

    messages = Message.objects.filter(buddies=buddy_obj)

    unread_count = 0
    for message in messages:
        if message.unread:
            if user_is_requester and not message.from_requester:
                unread_count += 1
            elif not user_is_requester and message.from_requester:
                unread_count += 1
    return unread_count

def get_conversation(request, buddy_name, read_mode):
    try:
        buddy_obj_tuple = get_buddy_obj(request.user, buddy_name)
        if len(buddy_obj_tuple) == 0:
            return JsonResponse({})

        buddy_obj = buddy_obj_tuple[0]
        user_is_requester = buddy_obj_tuple[1]

        messages = Message.objects.filter(buddies=buddy_obj)
        convo = []
        for message in messages:
            if user_is_requester:
                convo.append({
                    "left": not message.from_requester,
                    "content": message.content,
                    "sequence": message.sequence
                })
            else:
                convo.append({
                    "left": message.from_requester,
                    "content": message.content,
                    "sequence": message.sequence
                })

        mark_all_as_read = read_mode == "read"
        if mark_all_as_read:
            for message in messages:
                if user_is_requester and not message.from_requester and message.unread:
                    message.unread = False
                    message.save()
                elif not user_is_requester and message.from_requester and message.unread:
                    message.unread = False
                    message.save()

        if user_is_requester:
            num_unread = get_num_unread(buddy_obj.requestee, request.user)
        else:
            num_unread = get_num_unread(buddy_obj.requester, request.user)
        return JsonResponse({
            "conversation": convo,
            "numMessages": len(convo),
            "numUnread": num_unread
        })
    except:
        return JsonResponse({})

def new_message(request):
    buddy_obj_tuple = get_buddy_obj(request.user, request.POST.get("buddy_name"))
    if len(buddy_obj_tuple) == 0:
        return HttpResponse()

    buddy_obj = buddy_obj_tuple[0]
    user_is_requester = buddy_obj_tuple[1]

    sequence = Message.objects.filter(buddies=buddy_obj).count() + 1
    
    message = Message(
        unread=True,
        content=request.POST.get("content"),
        sequence=sequence,
        from_requester=user_is_requester,
        buddies=buddy_obj
        )
    message.save()
    return HttpResponse()