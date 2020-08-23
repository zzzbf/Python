from django.db import models
from django.urls import reverse

'''教师信息表'''
class Teacher(models.Model):
    tno = models.CharField(db_column='Tno', primary_key=True, max_length=5)  # Field name made lowercase.
    tname = models.CharField(db_column='Tname', max_length=20)  # Field name made lowercase.

    def __str__(self):
        return self.tname+ "(%s)"%self.tno
    
    class Meta:
        managed = False
        db_table = 'Teacher'
        verbose_name_plural = '教师信息表'
        verbose_name = '教师'
'''学生信息表'''
class Student(models.Model):
    sno = models.CharField(db_column='Sno', primary_key=True, max_length=8)  # Field name made lowercase.
    sname = models.CharField(db_column='Sname', max_length=20)  # Field name made lowercase.
    ssex = models.CharField(db_column='Ssex', max_length=2)  # Field name made lowercase.
    sbirth = models.CharField(db_column='Sbirth', max_length=10, blank=True, null=True)  # Field name made lowercase.
    sclass = models.CharField(db_column='Sclass', max_length=6, blank=True, null=True)  # Field name made lowercase.
    sdept = models.CharField(db_column='Sdept', max_length=20, blank=True, null=True)  # Field name made lowercase.

    def __str__(self):
        return self.sname+ "(%s)"%self.sno
    
    class Meta:
        managed = False
        db_table = 'Student'
        verbose_name_plural = '学生信息表'
        verbose_name = '学生'
'''管理员信息表'''
class Admin(models.Model):
    ano = models.CharField(db_column='Ano', primary_key=True, max_length=4)  # Field name made lowercase.
    name = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Admin'
        verbose_name_plural = '管理员信息表'
        verbose_name = '管理员'
    def __str__(self):
        return self.name+"(%s)"%self.ano
'''课程表'''
class Course_Base(models.Model):
    cname = models.CharField(db_column='Cname', max_length=50, blank=True, null=True)  # Field name made lowercase.
    ctype = models.CharField(db_column='Ctype', max_length=30, blank=True, null=True)  # Field name made lowercase.
    ccode = models.CharField(db_column='Ccode', primary_key=True, max_length=8)  # Field name made lowercase.
    cbrief = models.CharField(db_column='Cbrief', max_length=2500, blank=True, null=True)  # Field name made lowercase.

    def __str__(self):
        return self.cname+ "(%s)"%self.ccode
    
    class Meta:
        managed = False
        db_table = 'Course_Base'
        verbose_name_plural = '课程表'
        verbose_name = '课程'
'''2018-2019第一学期排课表'''
class Course_2018_2019_1(models.Model):
    cname = models.CharField(db_column='Cname', max_length=50)  # Field name made lowercase.
    ctype = models.CharField(db_column='Ctype', max_length=30)  # Field name made lowercase.
    ccode_base = models.ForeignKey('Course_Base', models.DO_NOTHING, db_column='Ccode_base')  # Field name made lowercase.
    ccredit = models.FloatField(db_column='Ccredit', blank=True, null=True)  # Field name made lowercase.
    ccode = models.CharField(db_column='Ccode', primary_key=True, max_length=35)  # Field name made lowercase.
    cposition = models.CharField(db_column='Cposition', max_length=40, blank=True, null=True)  # Field name made lowercase.
    cdept = models.CharField(db_column='Cdept', max_length=40, blank=True, null=True)  # Field name made lowercase.
    ctime = models.CharField(db_column='Ctime', max_length=50, blank=True, null=True)  # Field name made lowercase.
    tname = models.CharField(db_column='Tname', max_length=30, blank=True, null=True)  # Field name made lowercase.
    ccapacity = models.IntegerField(db_column='Ccapacity', blank=True, null=True)  # Field name made lowercase.
    selected = models.IntegerField(blank=True, null=True)
    def __str__(self):
        return self.cname+ "(%s)"%self.ccode
    class Meta:
        managed = False
        db_table = 'Course_2018_2019_1'
        verbose_name_plural = '授课计划表(2018-2019年第1学期)'
        verbose_name = '课程'
'''2018-2019第二学期排课表'''
class Course_2018_2019_2(models.Model):
    cname = models.CharField(db_column='Cname', max_length=50)  # Field name made lowercase.
    ctype = models.CharField(db_column='Ctype', max_length=30)  # Field name made lowercase.
    ccode_base = models.ForeignKey('Course_Base', models.DO_NOTHING, db_column='Ccode_base')  # Field name made lowercase.
    ccredit = models.FloatField(db_column='Ccredit', blank=True, null=True)  # Field name made lowercase.
    ccode = models.CharField(db_column='Ccode', primary_key=True, max_length=35)  # Field name made lowercase.
    cposition = models.CharField(db_column='Cposition', max_length=40, blank=True, null=True)  # Field name made lowercase.
    cdept = models.CharField(db_column='Cdept', max_length=40, blank=True, null=True)  # Field name made lowercase.
    ctime = models.CharField(db_column='Ctime', max_length=50, blank=True, null=True)  # Field name made lowercase.
    tname = models.CharField(db_column='Tname', max_length=30, blank=True, null=True)  # Field name made lowercase.
    ccapacity = models.IntegerField(db_column='Ccapacity', blank=True, null=True)  # Field name made lowercase.
    selected = models.IntegerField(blank=True, null=True)
    def __str__(self):
        return self.cname+ "(%s)"%self.ccode
    class Meta:
        managed = False
        db_table = 'Course_2018_2019_2'
        verbose_name_plural = '授课计划表(2018-2019年第2学期)'
        verbose_name = '课程'
'''本学期选课表'''
class Enroll(models.Model):
    sno = models.ForeignKey('Student', models.DO_NOTHING, db_column='Sno')  # Field name made lowercase.
    ccode = models.CharField(db_column='Ccode', max_length=35)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Enroll'
        verbose_name_plural = '选课表'
        verbose_name = '学生-课程'
    def __str__(self):
        return self.sno.sno+ "(%s)"%self.ccode
'''学生成绩表'''
class SC(models.Model):
    sno = models.ForeignKey('Student', models.DO_NOTHING, db_column='Sno')  # Field name made lowercase.
    ccode = models.CharField(db_column='Ccode', max_length=35, blank=True, null=True)  # Field name made lowercase.
    sscore = models.IntegerField(db_column='Sscore', blank=True, null=True)  # Field name made lowercase.
    make_up_exam = models.SmallIntegerField(blank=True, null=True)
    retake = models.SmallIntegerField(blank=True, null=True)

    def __str__(self):
        if '(2018-2019-1)' in self.ccode:
            return self.sno.sname+ "(%s)"%Course_2018_2019_1.objects.get(ccode=self.ccode).cname
        elif  '(2018-2019-2)' in self.ccode:
            return self.sno.sname+ "(%s)"%Course_2018_2019_2.objects.get(ccode=self.ccode).cname
        else:
            return ''
    def getPoint(self):
        if not self.sscore or isinstance(self.sscore,str):
            return ""
        if self.sscore>=95:
            return 5.0
        elif  self.sscore>=60:
            return 5.0-(95-self.sscore)*0.1
        else:
            return "不及格"
    
    class Meta:
        managed = False
        db_table = 'SC'
        verbose_name_plural = '学生-课程-成绩表'
        verbose_name = '学生-课程'
'''教师授课表'''
class TC(models.Model):
    tno = models.ForeignKey('Teacher', models.DO_NOTHING, db_column='Tno')  # Field name made lowercase.
    ccode = models.CharField(db_column='Ccode', max_length=35)  # Field name made lowercase.

    def __str__(self):
        return self.tno.tno+ "(%s)"%self.ccode
    class Meta:
        managed = False
        db_table = 'TC'
        verbose_name_plural = '教师-课程表'
        verbose_name = '教师'
'''学生毕业表'''
class StudentGraduate(models.Model):
    sno = models.OneToOneField(Student, models.DO_NOTHING, db_column='Sno',primary_key=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'StudentGraduate'
        verbose_name_plural = '学生毕业表'
        verbose_name = '学生'
    def __str__(self):
        return "%s(%s)"%(self.sno.sname,self.sno.sno)
'''学生退学表'''
class StudentQuit(models.Model):
    sno = models.OneToOneField(Student, models.DO_NOTHING, db_column='Sno',primary_key=True)  # Field name made lowercase.

    def __str__(self):
        return "%s(%s)"%(self.sno.sname,self.sno.sno)
    class Meta:
        managed = False
        db_table = 'StudentQuit'
        verbose_name_plural = '学生退学表'
        verbose_name = '学生'
'''学生退学警告表'''
class Dropoutalert(models.Model):
    sno = models.ForeignKey('Student', models.DO_NOTHING, db_column='Sno')  # Field name made lowercase.
    year = models.IntegerField()
    semester = models.SmallIntegerField()

    def __str__(self):
        return self.sno.sname+"(%s)"%self.sno.sno
    class Meta:
        managed = False
        db_table = 'DropOutAlert'
        verbose_name_plural = '学生退学警告表'
        verbose_name = '学生'

    
'''时间翻译表'''
class Ctime(models.Model):
    content = models.CharField(max_length=20, blank=True, null=True)
    row = models.SmallIntegerField(blank=True, null=True)
    col = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Ctime'
'''网络工程2017级培养计划'''
class Networkengineering_2017(models.Model):
    ccode = models.CharField(db_column='Ccode', max_length=8)  # Field name made lowercase.
    credit = models.FloatField(db_column='Credit')  # Field name made lowercase.

    def __str__(self):
        return self.ccode+ "(学分:%s)"%self.credit
    class Meta:
        managed = False
        db_table = 'NetworkEngineering_2017'
        verbose_name_plural = '网络工程2017级培养计划'
        verbose_name = '课程'