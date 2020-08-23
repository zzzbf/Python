from django import forms
from django.utils.translation import ugettext_lazy as _
from . import models

class UploadFileForm(forms.Form):
    score_file = forms.FileField(label="上传成绩文件",required=False)
class SC_Form(forms.ModelForm):
    sscore= getattr(models.SC,"sscore")
    class Meta:
        model=models.SC
        fields = "__all__"
        labels = {
            "point":"绩点",
            "sno":"学号",
            "ccode":"课程号",
            "sscore":"成绩"}