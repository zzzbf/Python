from django.shortcuts import render
from django.contrib.auth import authenticate,login,logout
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from .forms import LoginForm

import pymssql

'''身份'''
class Identity:
    def __init__(self,num):
        self.number = num
    def isTeacher(self):
        if self.number==2:
            return True
        return False
    def isStudent(self):
        if self.number==1:
            return True
        return False
def getName(request):
    conn = pymssql.connect(host='127.0.0.1',
                       user='',
                       password='',
                       database='',
                       charset="utf8")

    cursor = conn.cursor()
    '''学生'''
    if len(request.user.username)==8:
        sql = 'SELECT Sname FROM Student where Sno = %s'%(request.user.username)
        cursor.execute(sql)
        return cursor.fetchone()[0]

    '''教师'''
    if len(request.user.username)==5:
        sql = 'SELECT Tname FROM Teacher where Tno = %s'%(request.user.username)
        cursor.execute(sql)
        return cursor.fetchone()[0]



def user_login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/cas/home')
    if request.method=='POST':#如果用户通过post方法访问
        form=LoginForm(request.POST)
        if form.is_valid():#判断合法性
            cd=form.cleaned_data
            user=authenticate(
                username=cd['username'],
                password=cd['password'],
                )
            if user is not None:#判断用户存在性
                if user.is_active:#判断用户有效性
                    login(request,user)
                    request.session['name'] = getName(request)
                    
                    return HttpResponseRedirect('/cas/home')
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form=LoginForm()
        request.session['from'] = request.META.get('HTTP_REFERER', '/')
    return render(request,'account/login.html',{'form':form})
def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')
