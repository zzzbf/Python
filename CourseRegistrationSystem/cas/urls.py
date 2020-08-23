from django.urls import path
from . import views

app_name = 'cas'
urlpatterns = [
    path('home/',views.home,name='home'),
    path('course/',views.course,name='course'),
    path('score/',views.scoreQuery,name='scoreQuery'),
    path('timetable/',views.timetable,name='timetable'),
    path('searchInfo/',views.searchInfo,name='searchInfo'),
    path('make-up-exam/<Ccode>',views.makeUpExam,name='makeUpExam'),
    path('search/',views.search,name='search'),
    path('course-detail/<Ccode>',views.courseDetail,name='courseDetail'),
    path('student-score-insert/<Ccode>',views.studentScoreInsert,name='studentScoreInsert')
    ]
