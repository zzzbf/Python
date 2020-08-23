from django.contrib import admin
from django.urls import path
from .models import *
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.http import HttpResponse,HttpResponseRedirect
from .forms import *
import pymssql

INIT_FROM_YEAR = 2018

FROM_YEAR = 2018
TO_YEAR = 2019
SEMESTER = 2

conn = pymssql.connect(host='127.0.0.1',
                       user='',
                       password='',
                       database='',
                       charset="utf8")

cursor = conn.cursor()

dept_dict = {
    '网络工程':'NetworkEngineering_2017'}
def isGraduate(Sno,Sdept):
    tmpCode = {}
    # 查看培养计划
    if Sdept not in dept_dict:
        return False
    sql = "select * from %s "%(dept_dict[Sdept])
    cursor.execute(sql)
    plan_list = cursor.fetchall()
    for course in plan_list:
        code = course[0]
        credit = course[2]
        # 学生是否选择了该课程
        if '*' in  code:
            if code.strip("*") not in tmpCode:
                tmpCode[code.strip("*")]=0
            tmpCode[code.strip("*")]+=1
        else:
            sql = "select * from SC where Sno='%s' and Sscore>=60 and Ccode like '%%%s%%'"%(Sno,code)
            cursor.execute(sql)
            if not cursor.fetchone():
                return False
    
    for u,v in tmpCode.items():
        sql = "select * from SC where Sno='%s' and Sscore>=60 and Ccode like '%%%s%%'"%(Sno,u)
        cursor.execute(sql)
        if len(cursor.fetchall())<v:
            return False
    return True
def isQuit(Sno):
    sql = "select year,semester from DropOutAlert where Sno='%s' order by year,semester asc "%Sno
    cursor.execute(sql)
    student = cursor.fetchall()
    if not student:
        return False
    if len(student) == 1:
        return False
    preYear,preSemester = student[0]
    count = 1
    for student_meta in student[1:]:
        year,semester = student_meta
        count += 1
        if (year-preYear) == 1 and (semester-preSemester) == -1:
            return True
        elif (year-preYear) == 0 and (semester-preSemester) == 1:
            return True
        elif count>=3:
            return True
        else:
            preYear = year
            preSemester = semester
    return False
def isQuitAlert():
    #基本学分小于14
    sql='''select tmp.Sno,Sname,Ssex,Sclass,Sdept,credit from Student,
        (
	        select Sno ,SUM(Ccredit) credit from SC,Course_2018_2019_2  where  
	        SC.Ccode=Course_%d_%d_%d.Ccode and Sscore>=60 
	        group by Sno  having sum(Ccredit)<14
        ) tmp where Student.Sno=tmp.Sno and tmp.sno not in 
        (
            select Sno from DropOutAlert where year=%d 
            and semester=%d
        )
        '''%(FROM_YEAR,TO_YEAR,SEMESTER,FROM_YEAR,SEMESTER)
    cursor.execute(sql)
    return cursor.fetchall()

class StudentgraduateAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add/', self.my_view),
        ]
        return my_urls + urls

    def my_view(self, request):
        if request.method=="POST":
            student_graduated = request.POST.getlist('student')
            for sno in student_graduated:
                sql = "INSERT StudentGraduate VALUES('%s')"%sno
                cursor.execute(sql)
            conn.commit()
            return HttpResponseRedirect("/admin/cas/studentgraduate/")
        context = dict(
           self.admin_site.each_context(request),
        )
        sql = '''select Sno,Sname,Ssex,Sclass,Sdept from Student 
                 where Sno not in
                 (
                 select Sno from StudentGraduate
                 )
              '''
        cursor.execute(sql)
        Students = cursor.fetchall()
        context['Student_Graduated']=[]
        for student in Students:
            if isGraduate(student[0],student[4]):
                context['Student_Graduated'].append(student)
        return TemplateResponse(request, 'admin/Studentgraduate.html',context)
class StudentquitAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add/', self.my_view),
        ]
        return my_urls + urls

    def my_view(self, request):
        if request.method=="POST":
            student_quited = request.POST.getlist('student')
            if student_quited:
                for sno in student_quited:
                    sql = "INSERT StudentQuit VALUES('%s')"%sno
                    cursor.execute(sql)
                conn.commit()
            student_alert = request.POST.getlist('student-alert')
            if student_alert:
                for sno in student_alert:
                    sql = "INSERT DropOutAlert (sno,year,semester)VALUES('%s','%s','%s')"%(sno,FROM_YEAR,SEMESTER)
                    cursor.execute(sql)
                conn.commit()
            return HttpResponseRedirect("/admin/cas/studentquit/")
        context = dict(
           self.admin_site.each_context(request),
        )
        sql = '''select Sno,Sname,Ssex,Sclass,Sdept from Student where
                 Sno not in
                 (
                 select Sno from StudentQuit
                 )
              '''
        cursor.execute(sql)
        Students = cursor.fetchall()
        context['Student_Quited']=[]
        for student in Students:
            if isQuit(student[0]):
                context['Student_Quited'].append(student)

        context['Alert_Student'] = isQuitAlert()
       
        return TemplateResponse(request, 'admin/Studentquit.html',context)
class SCAdmin(admin.ModelAdmin):
    form = SC_Form
    readonly_fields=('point',)
    search_fields = ('sno__sno', 'ccode','sno__sname' )
    def point(self, SC):
        return SC.getPoint()

class StudentAdmin(admin.ModelAdmin):
    search_fields = ('sno', 'sname','ssex','sclass','sdept')
class TeacherAdmin(admin.ModelAdmin):
    search_fields = ('tno', 'tname' )
class AdminAdmin(admin.ModelAdmin):
    search_fields = ('ano', 'name' )
class Course_BaseAdmin(admin.ModelAdmin):
    search_fields = ('cname','ctype','ccode')
class Course_Course_2018_2019_1Admin(admin.ModelAdmin):
    search_fields = ('cname','ctype','ccode_base__ccode','cdept','ctime','tname')
class Course_Course_2018_2019_2Admin(admin.ModelAdmin):
    search_fields = ('cname','ctype','ccode_base__ccode','cdept','ctime','tname')
class TCAdmin(admin.ModelAdmin):
    search_fields=('tno__tno','ccode')
class EnrollAdmin(admin.ModelAdmin):
    search_fields=('sno__sno','ccode')
class DropoutalertAdmin(admin.ModelAdmin):
    search_fields=('sno',)


admin.site.register(Course_Base,Course_BaseAdmin)
admin.site.register(Course_2018_2019_1,Course_Course_2018_2019_1Admin)
admin.site.register(Course_2018_2019_2,Course_Course_2018_2019_2Admin)
admin.site.register(SC,SCAdmin)
admin.site.register(Student,StudentAdmin)
admin.site.register(Teacher,TeacherAdmin)
admin.site.register(Admin,AdminAdmin)
admin.site.register(TC,TCAdmin)
admin.site.register(StudentQuit,StudentquitAdmin)
admin.site.register(StudentGraduate,StudentgraduateAdmin)
admin.site.register(Enroll,EnrollAdmin)
admin.site.register(Dropoutalert,DropoutalertAdmin)

'''培养计划'''
admin.site.register(Networkengineering_2017)

