from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.template import loader, Context

from random import choice
from string import *

from compsoc.memberinfo.models import *
from compsoc.shortcuts import template_mail
from compsoc.settings import *

@login_required()
def index(request):

    # catch a DoesNotExist exception
    # and convert it to a falsehood
    def failsafe(f,val):
        try: return f()
        except: return val

    # is there a non-fail reduce function
    def getQuota(st): 
       return reduce(lambda acc,q:acc+q.quantity,u.quota_set.filter(status=st),0)

    u = request.user
    shell = failsafe(lambda: u.shellaccount,False)
    db = failsafe(lambda: u.databaseaccount,False)
    name = failsafe(lambda: u.nicknamedetails.nickname,"")
    website = failsafe(lambda: u.websitedetails,False)
    pub = failsafe(lambda: u.member.showDetails,False)

    quota,req_quota = (getQuota('PR'),getQuota('RE'))

    my_lists = u.mailinglist_set.all()
    other_lists = []
    for list in MailingList.objects.all():
        if list not in my_lists:
            other_lists.append(list.list)

    dict = {
        'shell': shell,
        'db': db,
        'quota': quota,
        'req_quota': req_quota*500,
        'total_quota':quota*500+1000,
        'name':name,
        'url':website.websiteUrl if website else "",
        'title':website.websiteTitle if website else "",
        'my_lists':my_lists,
        'other_lists':other_lists,
        'publish_details': pub,
        'user':u,
    }
    return render_to_response('memberinfo/index.html',dict)

@login_required()
def shell(request):
    return do_service(request,'shell',ShellAccount, 'shell',
        lambda acc: "You already own a shell account called %s" % acc.name)

@login_required()
def database(request):
    return do_service(request,'db',DatabaseAccount, 'database',
        lambda acc: "You already own a database account called %s" % acc.name)

def do_service(request,param,klass,name,error):
    n = request.POST[param]
    u = request.user

    try:
        acc = klass.objects.get(user=u)
        return render_to_response('memberinfo/request_error.html',
            {'user':u,'name':name,'error':error(acc)})
    except klass.DoesNotExist:
        obj = klass(user=u,name=n,status='RE')
        obj.save()

        template_mail(
            'New service request',
            'memberinfo/service_techteam.html',
            {'realname':("%s %s"%(u.first_name,u.last_name)),'username':n,'what':name},
            COMPSOC_TECHTEAM_EMAIL,
            [COMPSOC_TECHTEAM_EMAIL])
    return HttpResponseRedirect('/member/')

@login_required()
def quota(request):
    amount = request.POST['quota']
    user = request.user
    try:
        acc_name = user.shellaccount.name
        q = Quota(user=user,quantity=amount,status='RE')
        q.save()
        template_mail(
            'Quota request',
            'membeinfo/quota_techteam',
            {'realname':("%s %s"%(u.first_name,u.last_name)),'username':acc_name,'amount':amount},
            user.email,
            [COMPSOC_TECHTEAM_EMAIL,COMPSOC_TREASURER_EMAIL])
        return HttpResponseRedirect('/member/')
    except ValueError:
        return render_to_response('memberinfo/request_error.html',
            {'user':user,'name':'Quota','error':"%s is not an integer" % amount})
    except ShellAccount.DoesNotExist:
        return render_to_response('memberinfo/request_error.html',
            {'user':user,'name':'Quota','error':'You don\'t have a shell account'})

@login_required()
def lists(request):
    my_lists = request.user.mailinglist_set
    my_lists.clear()
    for mlist in MailingList.objects.all():
        if request.POST.has_key(mlist.list):
            my_lists.add(mlist)
    print "my_lists contains: ", my_lists.all()

    request.user.save()
    print "request.user.mailinglist_set contains: ", request.user.mailinglist_set.all()
    return HttpResponseRedirect('/member/')

@login_required()
def details(request):
    u = request.user
    name = request.POST['name']
    url = request.POST['url']
    title = request.POST['title']
    try: publish = request.POST['publish']
    except: publish = False

    member = u.member
    member.showDetails = publish
    member.save()

    try:
        nickname = u.nicknamedetails
        nickname.nickname = name
    except NicknameDetails.DoesNotExist:
        nickname = NicknameDetails(user=u, nickname=name)
    nickname.save()

    try:
        website = u.websitedetails
        website.websiteTitle = title
        website.websiteUrl = url
    except WebsiteDetails.DoesNotExist:
        website = WebsiteDetails(user=u,websiteTitle=title,websiteUrl=url)
    website.save()
    
    return HttpResponseRedirect('/member/')

def member_list(request):
    users = []

    def get_website(user,f):
        try:
            return f(user.websitedetails)
        except WebsiteDetails.DoesNotExist:
            return False

    for user in User.objects.all():
        if user.member.showDetails and user.is_active:
            users.append((
                user.get_full_name(),
                user.member.get_nick(),
                get_website(user,lambda w: w.websiteTitle),
                get_website(user,lambda w: w.websiteUrl),
            ))
    
    dict = {
        'user': request.user,
        'users': users
    }
    return render_to_response('memberinfo/list.html',dict)

def reset_password(request):
    try:
        # Do the password reset
        user_name = request.POST['user_name']
        user = User.objects.get(username__exact=user_name)
        password = user.make_random_password()
        user.save()

        # Email the user
        template_mail(
            'Compsoc Password Reset',
            'memberinfo/reset_email',
            {'name':user_name,'password':password},
            COMPSOC_EXEC_EMAIL,
            [user.email])
        render_to_response('memberinfo/password_reset_success.html',{'user':request.user})
    # If someone tries to reset the password of a user who doesn't exist, then report it
    except User.DoesNotExist:
        template_mail(
            'Warning: Failed Password Reset Attempt',
            'memberinfo/techteam_reset_email',
            {'name':user_name, 'ip':request.META['REMOTE_ADDR']},
            COMPSOC_TECHTEAM_EMAIL,
            [COMPSOC_TECHTEAM_EMAIL])
        render_to_response('memberinfo/password_reset_no_name.html', {'tech':COMPSOC_TECHTEAM_EMAIL,})

@login_required()
def reset_account(request,account):
    try:
        u = request.user
        name = (u.databaseaccount if account == 'db' else u.shellaccount).name
        type = 'Database' if account == 'db' else 'Shell'
        template_mail(
            'Password reset request',
            'memberinfo/account_techteam_email',
            {'name':u.get_full_name(),'type':type,'accname':name},
            u.email,
            [COMPSOC_TECHTEAM_EMAIL])
        render_to_response('memberinfo/account_reset.html')
    except DatabaseAccount.DoesNotExist:
        return render_to_response('memberinfo/request_error.html',
            {'user':u,'name':'Database','error':"You don't have a database, so it can't be password reset"})
    except ShellAccount.DoesNotExist:
        return render_to_response('memberinfo/request_error.html',
            {'user':u,'name':'Shell','error':"You don't have a shell account, so it can't be password reset"})
       
def create_guest(request):
    name = request.POST['name']
    email = request.POST['email']
    u = User.objects.create_user(name,email)
    u.set_unusable_password()
    u.is_active=False
    u.save()
    mem = Member.objects.create(user=u,guest=True,showDetails=False)
    mem.save()
    n = NicknameDetails(user=u,nickname=name)
    n.save()
    template_mail(
        'Guest account request',
        'memberinfo/guest_request_email',
        {'name':name},
        COMPSOC_EXEC_EMAIL,
        [email])
    template_mail(
        'Guest account request',
        'memberinfo/exec_guest_request_email',
        {'name':name},
        COMPSOC_EXEC_EMAIL,
        [COMPSOC_EXEC_EMAIL])
    return render_to_response('memberinfo/guest_request.html')


