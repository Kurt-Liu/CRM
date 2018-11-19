from .models import *
from stark.service.sites import site,ModelStark

site.register(School)
site.register(Order)
site.register(UserInfo)


class ClassConfig(ModelStark):
    list_display = ['course', 'semester', 'teachers', 'tutor']
site.register(ClassList,ClassConfig)

site.register(Customer)
site.register(ConsultRecord)
site.register(Student)
site.register(ClassStudyRecord)

class StudentStudyRecordConfig(ModelStark):
    list_display = ['student']

site.register(StudentStudyRecord,StudentStudyRecordConfig)
site.register(Department)
site.register(Course)
