import pymssql
import re

from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger

from django import forms
from .models import *
from .forms import UploadFileForm



conn = pymssql.connect(host='127.0.0.1',
                       user='',
                       password='',
                       database='',
                       charset="utf8")

cursor = conn.cursor()

INIT_FROM_YEAR = 2018

FROM_YEAR = 2018
TO_YEAR = 2019
SEMESTER = 2

pattern1 = "(.*?){第(.*?)-(.*?)周};(.*?){"
pattern2 = "(.*?){第(.*?)-(.*?)周\|(.*?)周}"
pattern3 = "(.*?){第(.*?)-(.*?)周}"

'''课程类'''
class Course:
    def __init__(self,row,col,name,teacher,position,time,section):
        self.row = row
        self.col = col
        self.name = name
        self.time = time
        self.teacher = teacher
        self.position = position
        self.section = section

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

'''检查课程冲突'''
def isTimeConflict(time,Sno):
    if ';' in time:
        ctime_ = time.split(';')
    else:
        ctime_ = [time]
    for time in ctime_:
        ctime = re.findall(r'周(.*?)第(.*?)节{第(.*?)-(.*?)周(.*)}',time)[0]
        ctime = list(ctime)
        if len(ctime[4])==0:
            ctime[4]=0
        elif '单' in ctime[4]:
            ctime[4]=1
        else:
            ctime[4]=2
        date,from_to,from_week,to_week,timetype =  ctime
        sql = '''
             select * from Course_%d_%d_%d,Enroll 
             where Course_%d_%d_%d.Ccode=Enroll.Ccode 
             and Sno='%s' 
             and Ctime like '%%周%s第%s%%' 
            '''%(FROM_YEAR,TO_YEAR,SEMESTER,FROM_YEAR,TO_YEAR,SEMESTER,Sno,date,from_to)
        cursor.execute(sql)
        # 时间一致
        if cursor.fetchone():
            if timetype == 0:
                return True
            else:
                #判断单双周:
                t = time.split('|')[-1][-3]
                if t == '双':
                    sql = '''
                            select * from Course_%d_%d_%d,Enroll 
                            where Course_%d_%d_%d.Ccode=Enroll.Ccode 
                            and Sno='%s' and Ctime like '%%周%s第%s%%|%s%%'
                        '''%(FROM_YEAR,TO_YEAR,SEMESTER,FROM_YEAR,TO_YEAR,SEMESTER,Sno,date,from_to,'双')
                else:
                    sql = '''
                            select * from Course_%d_%d_%d,Enroll 
                            where Course_%d_%d_%d.Ccode=Enroll.Ccode 
                            and Sno='%s' and Ctime like '%%周%s第%s%%|%s%%'
                        '''%(FROM_YEAR,TO_YEAR,SEMESTER,FROM_YEAR,TO_YEAR,SEMESTER,Sno,date,from_to,'单')
                cursor.execute(sql)
                if cursor.fetchone():
                    return True
                return False
        return False

'''获取名字'''
def getName(request):
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


'''首页视图'''
def home(request):
    '''是否已登录'''
    if request.user.is_authenticated:
        if request.method=='POST':
            # 学生退课
            if len(request.user.username) == 8:
                selectedCourse = request.POST.getlist('course')
                for course in selectedCourse:
                    sql = "delete from Enroll where Sno = '%s' and Ccode = '%s'"%(request.user.username,course)
                    cursor.execute(sql)
                    
                    sql = "select selected from Course_%d_%d_%d where Ccode='%s'"%(FROM_YEAR,TO_YEAR,SEMESTER,course)
                    cursor.execute(sql)
                    # 原容量
                    pre_cap = cursor.fetchone()[0]
                    sql = "update Course_%d_%d_%d set selected=%d where Ccode='%s'"%(FROM_YEAR,TO_YEAR,SEMESTER,pre_cap-1,course)
                    cursor.execute(sql)
                conn.commit()
                # 暂时转到首页
                return HttpResponseRedirect('/cas/home')
        # 学生
        if len(request.user.username)==8:
            # 查找已选课程
            if request.GET.get('q'):
                sql = '''select Cname,Ccredit,Ctype,Tname,Enroll.Ccode,Ctime,Cposition,Cdept 
                 from Enroll,Course_%d_%d_%d
                 where Enroll.Ccode = Course_%d_%d_%d.Ccode 
                 and Sno='%s' and Cname like('%%%s%%')
                 '''%(FROM_YEAR,TO_YEAR,SEMESTER,FROM_YEAR,TO_YEAR,SEMESTER,request.user.username,request.GET['q'])
            # 已选课程
            else:
                sql = '''select Cname,Ccredit,Ctype,Tname,Enroll.Ccode,Ctime,Cposition,Cdept 
                         from Enroll,Course_%d_%d_%d
                         where Enroll.Ccode = Course_%d_%d_%d.Ccode 
                         and Sno='%s'
                      '''%(FROM_YEAR,TO_YEAR,SEMESTER,FROM_YEAR,TO_YEAR,SEMESTER,request.user.username)
            identity = 1
                    
        # 教师
        if len(request.user.username)==5:
            # 查找已开课程
            if request.GET.get('q'):
                sql = '''select  Cname,Ccredit,Ctype,Tname,TC.Ccode,Ctime,Cposition,Cdept
                         from TC,Course_%d_%d_%d
                         where Course_%d_%d_%d.Ccode=TC.Ccode and TC.Tno='%s'
                         and Cname like ('%%%s%%')
                         '''%(FROM_YEAR,TO_YEAR,SEMESTER,FROM_YEAR,TO_YEAR,SEMESTER,request.user.username,request.GET['q'])
            # 已开课程
            else:
                sql = '''select  Cname,Ccredit,Ctype,Tname,TC.Ccode,Ctime,Cposition,Cdept
                         from TC,Course_%d_%d_%d
                         where Course_%d_%d_%d.Ccode=TC.Ccode and TC.Tno='%s'
                         '''%(FROM_YEAR,TO_YEAR,SEMESTER,FROM_YEAR,TO_YEAR,SEMESTER,request.user.username)
            identity = 2
                
        cursor.execute(sql)
        courseData = cursor.fetchall()
            
        # 分页
        paginator = Paginator(courseData,20)
        page = request.GET.get('page')
        try:
            courses = paginator.page(page)
        except PageNotAnInteger:
            courses = paginator.page(1)
        except EmptyPage:
            courses = paginator.page(paginator.num_pages)     
        return render(request,'cas/Home.html',
                      {'courses':courses,
                        'page':page,
                        'name':request.session['name'],
                        'identity':Identity(identity)
                       })
    # 没有认证过，转到登录页面
    else:
        return HttpResponseRedirect('/')

'''选课'''
def course(request):
    query = None
    # 首先检查用户是否认证过
    if request.user.is_authenticated:
        # 选课
        if request.method=='POST':
            selectedCourse = request.POST.getlist('course')
            for course in selectedCourse:
                sql = "select Ctime from Course_%d_%d_%d where Ccode='%s'"%(FROM_YEAR,TO_YEAR,SEMESTER,course)
                cursor.execute(sql)
                tmp = cursor.fetchone()[0]
                
                if isTimeConflict(tmp,request.user.username):
                    '''--同名课程过滤--'''
                    sql = '''
                         select Cname,Ccredit,Ctype,Tname,Ccode,Ctime,Cposition,Cdept,Ccapacity-selected ,Ccode_Base 
                         from Course_%d_%d_%d
                         where Course_%d_%d_%d.Ccode_base not in 
                         (
                           select Ccode_base from Course_%d_%d_%d,Enroll where 
                           Course_%d_%d_%d.Ccode=Enroll.Ccode and Sno = %s
                         ) 
                         '''%(FROM_YEAR,TO_YEAR,SEMESTER,
                                FROM_YEAR,TO_YEAR,SEMESTER,
                                FROM_YEAR,TO_YEAR,SEMESTER,
                                FROM_YEAR,TO_YEAR,SEMESTER,
                                request.user.username)
                    cursor.execute(sql)
                    courseData = cursor.fetchall()
                    paginator = Paginator(courseData,20)
                    page = request.GET.get('page')
                    '''--容量已满判断--'''
                    try:
                        courses = paginator.page(page)
                    except PageNotAnInteger:
                        courses = paginator.page(1)
                    except EmptyPage:
                        courses = paginator.page(paginator.num_pages)
                    return render(request,'cas/StudentCourse.html',
                                  {'courses':courses,
                                   'page':page,
                                   'name':getName(request),
                                   'identity':Identity(1),
                                   'query':None,
                                   'conflict':1,
                                   })
                
                # 原容量
                sql = "select Ccapacity,selected from Course_%d_%d_%d where Ccode='%s'"%(FROM_YEAR,TO_YEAR,SEMESTER,course)
                cursor.execute(sql)
                capacity,selected = cursor.fetchone()
                if selected >= capacity:
                    '''应提示用户容量不足'''
                    next = request.POST.get('next', '/')
                    return HttpResponseRedirect(next)
                # 导入选课数据
                sql = "insert  Enroll (Sno,Ccode) VALUES('%s','%s')"%(request.user.username,course)
                cursor.execute(sql)
                # 选课成功余量减一
                sql = "update Course_%d_%d_%d set selected=%d where Ccode='%s'"%(FROM_YEAR,TO_YEAR,SEMESTER,selected+1,course)
                cursor.execute(sql)
            conn.commit()
            next = request.POST.get('next', '/')
            return HttpResponseRedirect(next)
        # 查找课程或者查看课程
        if request.method=='GET':
            sql = '''
                  select Cname,Ccredit,Ctype,Tname,Ccode,Ctime,Cposition,Cdept,
                         Ccapacity-selected,Ccode_Base from Course_%d_%d_%d
                  where Course_%d_%d_%d.Ccode_base not in (
                      select Ccode_base from Course_%d_%d_%d,Enroll where 
                      Course_%d_%d_%d.Ccode=Enroll.Ccode and Sno = %s) 
                   '''%(FROM_YEAR,TO_YEAR,SEMESTER,
                        FROM_YEAR,TO_YEAR,SEMESTER,
                        FROM_YEAR,TO_YEAR,SEMESTER,
                        FROM_YEAR,TO_YEAR,SEMESTER,
                        request.user.username)
            cursor.execute(sql)
            courseData = cursor.fetchall()

            # 分页
            paginator = Paginator(courseData,20)
            page = request.GET.get('page')

            try:
                courses = paginator.page(page)
            except PageNotAnInteger:
                courses = paginator.page(1)
            except EmptyPage:
                courses = paginator.page(paginator.num_pages)
            return render(request,'cas/StudentCourse.html',
                          {'courses':courses,
                           'page':page,
                           'name':getName(request),
                           'identity':Identity(1),
                           'query':query,
                           })
    # 没有认证过，转到登录页面
    else:
        return HttpResponseRedirect('/')

'''老师导入成绩'''
def studentScoreInsert(request,Ccode):
    if request.user.is_authenticated and len(request.user.username)==5:
        if request.method=='POST':
            file = request.FILES.getlist('score_file')
            weights = float(request.POST['weights'])
            # 文件上传
            count = 1
            file = file[0]
            if file:
                try:
                    for line in file.open():
                        sno,usual_score, final_score= line.decode("utf-8").split(' ')
                        score =int((weights/(1+weights))*int(usual_score)+(1/(1+weights))*int(final_score))
                        sql = "insert SC (Sno,Ccode,Sscore) Values ('%s','%s','%s')"%(sno,Ccode,score)
                        cursor.execute(sql)
                    conn.commit()
                    next = request.POST.get('next', '/')
                    return HttpResponseRedirect(next)
                except Exception as e:
                    return HttpResponse(e)
            sql = "select Enroll.Sno,Sname from Enroll,Student where Ccode = '%s' and Enroll.Sno = Student.Sno "%Ccode
            cursor.execute(sql)
            students = cursor.fetchall()
            for student in students:
                if len(request.POST['%s-usual-score'%student[0]])!=0 and len(request.POST['%s-final-score'%student[0]])!=0:
                    usual_score = request.POST['%s-usual-score'%student[0]]
                    final_score = request.POST['%s-final-score'%student[0]]
                    score =int((weights/(1+weights))*int(usual_score)+(1/(1+weights))*int(final_score))
                    # 更新成绩
                    sql = "insert SC (Sno,Ccode,Sscore) Values ('%s','%s','%s')"%(student[0],Ccode,score)
                    cursor.execute(sql)
            conn.commit()
            return HttpResponseRedirect('/cas/home/')

        # 选该门课的学生的成绩
        sql = "select SC.Sno,Sname,Sscore from SC,Student where Ccode = '%s' and SC.Sno = Student.Sno"%Ccode
        cursor.execute(sql)
        registered=1
        students = cursor.fetchall()
        single=None
        try:
            if len(students[0])==8 and len(students)==3:
                single=1
        except Exception as e:
            pass
        if not students:
            sql = "select Enroll.Sno,Sname from Enroll,Student where Ccode = '%s' and Enroll.Sno = Student.Sno "%Ccode
            cursor.execute(sql)
            registered=None
            students = cursor.fetchall()
        return render(request,'cas/StudentScoreInsert.html',
                    {'students':students,'Ccode':Ccode,
                     'name':getName(request),'identity':Identity(2),
                      'form':UploadFileForm(),
                      'registered':registered,
                      'single':single,
                      'make_up_tag':None
                      })

#导入补考成绩
def makeUpExam(request,Ccode):
    if request.user.is_authenticated and len(request.user.username)==5:
        if request.method=='POST':
            file = request.FILES.getlist('score_file')
            # 文件上传
            count = 1
            if file:
                try:
                    for line in file[0].open():
                        sno,score= line.decode("utf-8").split(' ')
                        sql = "update SC set make_up_exam=%s where Sno='%s' and Ccode='%s'"%(int(score),sno,Ccode)
                        cursor.execute(sql)
                        conn.commit()
                    next = request.POST.get('next', '/')
                    return HttpResponseRedirect(next)
                except Exception as e:
                    return HttpResponse(e)
            sql = "select SC.Sno,Sname from SC,Student where Sscore<60 and Ccode = '%s' and SC.Sno = Student.Sno "%Ccode
            cursor.execute(sql)
            students = cursor.fetchall()
            for student in students:
                if len(request.POST['%s-score'%student[0]])!=0:
                    score = int(request.POST['%s-score'%student[0]])
                    # 更新成绩
                    sql = "update SC set make_up_exam=%s where Sno='%s' and Ccode='%s'"%(score,student[0],Ccode)
                    cursor.execute(sql)
            conn.commit()
            return HttpResponseRedirect('/cas/home/')

        #查询已导入补考成绩的学生
        sql="select SC.Sno,Sname,make_up_exam from SC,Student where Sscore<60 and Ccode = '%s' and SC.Sno = Student.Sno"%Ccode
        cursor.execute(sql)
        students=cursor.fetchall()
        single=None

        try:
            if len(students[0])==8 and len(students)==3:
                single=1
        except:
            #没有学生选这门课
            return HttpResponseRedirect("/cas/home")

        if not students[0][2]:
            sql = "select SC.Sno,Sname,Sscore from SC,Student where Sscore<60 and Ccode = '%s' and SC.Sno = Student.Sno"%Ccode
            cursor.execute(sql)
            registered=None
            students = cursor.fetchall()
        else:
            registered=1

        if not students:
            return HttpResponseRedirect("/cas/home")

        return render(request,'cas/StudentScoreInsert.html',
                    {'students':students,'Ccode':Ccode,
                     'name':getName(request),'identity':Identity(2),
                      'form':UploadFileForm(),
                      'registered':registered,
                      'single':single,
                      'make_up_tag':1
                      })


'''查询成绩'''
def scoreQuery(request):
    if request.user.is_authenticated:
        if len(request.user.username)==8:
            #选出课程名、成绩
            # 计算绩点
            gpa = []
            data = []
            for i in range(FROM_YEAR - INIT_FROM_YEAR + 1):
                for j in range(1,3):
                    if j>SEMESTER:
                        continue
                    sql = '''
                            select Cname,Sscore,Ccredit,make_up_exam,retake 
                            from Course_%d_%d_%d,SC
                            where Course_%d_%d_%d.Ccode=SC.Ccode
                            and Sno=%s
                          '''%(FROM_YEAR-i,TO_YEAR-i,j,FROM_YEAR-i,TO_YEAR-i,j,request.user.username)
                    cursor.execute(sql)
                    currentData = cursor.fetchall()
                    for d in currentData:
                        score = d[1]
                        if score:
                            try:
                                if score>=95:
                                    gpa.append(5.0)
                                elif score>=60:
                                    gpa.append(round(5.0-(95-score)*0.1,1))
                                else:
                                    gpa.append("不及格")
                            except:
                                gpa.append("")
                        else:
                            data[data.index(d)] = d[0]," ",d[2],"",""
                            gpa.append("")
                    data += currentData
            return render(request,'cas/score.html',
                          {'data':zip(data,gpa),
                           'name':getName(request),
                           'identity':Identity(1)
                           })
def courseDetail(request,courseCode):
    sql = "select * from Course where Ccode = '%s'"%courseCode
    cursor.execute(sql)
    pass

def searchInfo(request):
    if request.user.is_authenticated:
        if len(request.user.username)==8:
            sql = "select * from Student where Sno=%s"%(request.user.username)
            cursor.execute(sql)
            return render(request,
                    'cas/PersonInfo.html',{
                    'student':cursor.fetchall()[0],
                    'name':getName(request),
                    'identity':Identity(1)})
        if len(request.user.username)==5:
            sql = "select * from Teacher where Tno=%s"%(request.user.username)
            cursor.execute(sql)
            return render(request,
                    'cas/PersonInfo.html',{
                    'teacher':cursor.fetchall()[0],
                    'name':getName(request),
                    'identity':Identity(2)})


        
def outputSchedule(sno):
    courses_dict = {}
    sql = '''
             select Cname,Cposition,Ctime,Tname
             from Enroll,Course_%d_%d_%d
             where Sno='%s'
             and Enroll.Ccode=Course_%d_%d_%d.Ccode
             '''%(FROM_YEAR,TO_YEAR,SEMESTER,sno,FROM_YEAR,TO_YEAR,SEMESTER,)
    cursor.execute(sql)
    courses = cursor.fetchall()
    for c in courses:
        # 两个时间段,不必考虑单双周
        if ';' in c[2]:
            weektype = 0
            _time = re.findall(pattern1,c[2])[0]
            pos1,pos2 = c[1].split(';')
            sql = "select row,col from Ctime where content='%s'"%(_time[0])
            cursor.execute(sql)
            row,col = cursor.fetchone()
            courses_dict[7*row+col]=Course(row,col,c[0],c[3],pos1,c[2],_time[0].count(',')+1)
            
            
            sql = "select row,col from Ctime where content='%s'"%(_time[3])
            cursor.execute(sql)
            row,col = cursor.fetchone()
            courses_dict[7*row+col]=Course(row,col,c[0],c[3],pos2,c[2],_time[3].count(',')+1)
            
        else:
            
            time_info = re.findall(pattern2,c[2])
            if time_info:
                _time,begin_week,end_week,weektype = time_info[0]
                if weektype == '单':
                    weektype = 1
                else:
                    weektype = 2
            else:
                _time,begin_week,end_week = re.findall(pattern3,c[2])[0]
                weektype = 0
            sql = "select row,col from Ctime where content='%s'"%(_time)
            cursor.execute(sql)
            row,col = cursor.fetchone()
            
            courses_dict[7*row+col]=Course(row,col,c[0],c[3],c[1],c[2],_time.count(',')+1)
    return courses_dict
def timetable(request):
    return render(request,'cas/timetable.html',
                  {'courses':outputSchedule(request.user.username),
                   'name':getName(request),
                    'identity':Identity(1),
                    'count1':range(7),
                    'count2':range(7,14),
                    'count3':range(14,21),
                    'count4':range(21,28),
                    'count5':range(28,35),
                    }
                  )
type_dict = {1: '通识必修', 2: '校定必修', 3: '其它任选', 4: '专业必修', 5: '专业选修', 6: '实践', 7: '必修', 8: '科技任选', 9: '人文任选', 10: '学科必修', 11: '外语模块', 12: '实践必修', 13: '公共选修', 14: '实践选修', 15: '社会发展与公民教育', 16: '人文经典与人文修养', 17: '通识选修', 18: '创业教育', 19: '科技发展与科学精神', 20: '心理健康选修', 21: '文明对话与国际视野', 22: '经管任选', 23: '艺术创作与审美体验', 24: '英语必修', 25: '课外必修', 26: '专业限选', 27: '专业任选', 28: '公共必修'}

def search(request):
    if request.method=='POST':
            selectedCourse = request.POST.getlist('course')
            for course in selectedCourse:
                sql = "select Ctime from Course_%d_%d_%d where Ccode='%s'"%(FROM_YEAR,TO_YEAR,SEMESTER,course)
                cursor.execute(sql)
                tmp = cursor.fetchone()[0]
                if isTimeConflict(tmp,request.user.username):
                    '''--同名课程过滤--'''
                    sql = '''
                         select Cname,Ccredit,Ctype,Tname,Ccode,Ctime,Cposition,Cdept,Ccapacity-selected,Ccode_base  
                         from Course_%d_%d_%d
                         where Course_%d_%d_%d.Ccode_base not in 
                         (
                           select Ccode_base from Course_%d_%d_%d,Enroll where 
                           Course_%d_%d_%d.Ccode=Enroll.Ccode and Sno = %s
                         ) 
                         '''%(FROM_YEAR,TO_YEAR,SEMESTER,
                                FROM_YEAR,TO_YEAR,SEMESTER,
                                FROM_YEAR,TO_YEAR,SEMESTER,
                                FROM_YEAR,TO_YEAR,SEMESTER,
                                request.user.username)
                    cursor.execute(sql)
                    courseData = cursor.fetchall()
                    paginator = Paginator(courseData,20)
                    page = request.GET.get('page')
                    '''--容量已满判断--'''
                    try:
                        courses = paginator.page(page)
                    except PageNotAnInteger:
                        courses = paginator.page(1)
                    except EmptyPage:
                        courses = paginator.page(paginator.num_pages)
                    return render(request,'cas/StudentCourse.html',
                                  {'courses':courses,
                                   'page':page,
                                   'name':getName(request),
                                   'identity':Identity(1),
                                   'query':None,
                                   'conflict':1,
                                   })
                sql = "insert  Enroll (Sno,Ccode) VALUES('%s','%s')"%(request.user.username,course)
                cursor.execute(sql)
                # 选课成功容量减一
                sql = "select Ccapacity,selected from Course_%d_%d_%d where Ccode='%s'"%(FROM_YEAR,TO_YEAR,SEMESTER,course)
                cursor.execute(sql)
                # 原容量
                capacity,selected = cursor.fetchone()
                if selected >= capacity:
                    '''应提示用户容量不足'''
                    next = request.POST.get('next', '/')
                    return HttpResponseRedirect(next)
                sql = "update Course_%d_%d_%d set selected=%d where Ccode='%s'"%(FROM_YEAR,TO_YEAR,SEMESTER,selected+1,course)
                cursor.execute(sql)
            conn.commit()
            next = request.POST.get('next', '/')
            return HttpResponseRedirect(next)
    sql = ''' select Cname,Ccredit,Ctype,Tname,Ccode,Ctime,Cposition,Cdept,Ccapacity-selected,Ccode_base 
              from Course_%d_%d_%d
              where Course_%d_%d_%d.Ccode_base not in 
              (
              select Ccode_base from Course_%d_%d_%d,Enroll where 
              Course_%d_%d_%d.Ccode=Enroll.Ccode and Sno = %s
              ) 
               '''%(FROM_YEAR,TO_YEAR,SEMESTER,
                    FROM_YEAR,TO_YEAR,SEMESTER,
                    FROM_YEAR,TO_YEAR,SEMESTER,
                    FROM_YEAR,TO_YEAR,SEMESTER,
                    request.user.username)
    for key,value in request.GET.items():
        if value:
            if key=='option':
                if value=='0':
                    continue
                else:
                    sql+="and Ctype like '%%%s%%' "%(type_dict[int(value)])
            else:
                sql+="and %s like '%%%s%%' "%(key,value)
    cursor.execute(sql)
    courseData = cursor.fetchall()

    # 分页
    
    paginator = Paginator(courseData,20)
    page = request.GET.get('page')
    try:
        courses = paginator.page(page)
    except PageNotAnInteger:
        courses = paginator.page(1)
    except EmptyPage:
         courses = paginator.page(paginator.num_pages)
   
    return render(request,'cas/StudentCourse.html',
         {'courses':courses,
          'page':page,
          'name':getName(request),
          'identity':Identity(1),
          })
 
def courseDetail(request,Ccode):
    if request.user.is_authenticated:
        if len(request.user.username)==8:
            identity=1
        else:
            identity=2
        sql="select * from Course_Base where Ccode='%s'"%Ccode
        cursor.execute(sql)
        course=cursor.fetchone()
        return render(request,"cas/CourseDetail.html",
                      {"course":course,
                       'name':request.session['name'],
                       'identity':Identity(identity)
                       })
    return HttpResponse('/')
