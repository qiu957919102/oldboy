#!/usr/bin/env python  
#-*- coding:utf-8 -*-  

from .models import *
from Xadmin.service.Xadmin import site
from Xadmin.service.Xadmin import ModelXadmin
from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import render,redirect

class UserInfoConfig(ModelXadmin):
    list_display = ["name", "email", "depart"]

class ClassListConfig(ModelXadmin):

    def display_classname(self, obj=None, is_header=False):
        if is_header:
            return "班级名称"

        class_name = "%s(%s)"%(obj.course.name, str(obj.semester))
        return class_name

    list_display = [display_classname, "school", "tutor", "teachers"]


class CustomerConfig(ModelXadmin):
    def display_gender(self, obj=None, is_header=False):
        if is_header:
            return "性别"
        return obj.get_gender_display()

    def display_course(self, obj=None, is_header=False):
        if is_header:
            return "咨询课程"
        t_course = []
        for course in obj.course.all():
            s = "<a href='/Xadmin/crm/customer/cancel_course/{}/{}' style='border:1px solid #369;padding:3px 6px'><span>{}</span></a>&nbsp;".format(obj.pk, course.pk, course.name)
            t_course.append(s)
        return mark_safe("".join(t_course))

    list_display = ["name", display_gender, display_course, "consultant"]

    # 在某个特定表中用到的视图函数即url可以在该表的配置类中定义
    def cancel_course(self, request, customer_id, course_id):
        cancel_obj = Customer.objects.filter(pk=customer_id).first()
        cancel_obj.course.remove(course_id)
        return redirect(self.get_list_url())

    # 需要在原始类中添加同样的函数
    def extra_url(self):
        t_url = []
        t_url.append(url(r"cancel_course/(\d+)/(\d+)", self.cancel_course))

        return t_url

site.register(Department)
site.register(UserInfo, UserInfoConfig)
site.register(Course)
site.register(School)
site.register(ClassList, ClassListConfig)
site.register(Customer, CustomerConfig)

class ConsultRecordConfig(ModelXadmin):
    list_display = ["customer", "consultant", "note", "date"]

site.register(ConsultRecord, ConsultRecordConfig)


class StudentConfig(ModelXadmin):
    list_display = ["customer", "class_list"]
    list_display_links = ["customer"]

site.register(Student, StudentConfig)


class CourseRecordConfig(ModelXadmin):

    def score(self, request, course_record_id):
        if request.method == "POST":
            # 先看看传回来的数据长什么样
            print(request.POST)
            # 构建我们想要的数据结构
            dic_data = {}
            for key, value in request.POST.items():
                if key == "csrfmiddlewaretoken":continue

                # 将传来的key值分开
                field, pk = key.rsplit("_", 1)

                # 分两种情况存入dic_data中，已有字段和无字段
                if pk in dic_data:# 有字段
                    dic_data[pk][field] = value
                else:# 无字段
                    dic_data[pk] = {field: value}

            # 更新数据库
            for pk, update_data in dic_data.items():
                StudyRecord.objects.filter(pk=pk).update(**update_data)

            # 返回当前页面
            return redirect(request.path)
        else:

            study_record_list = StudyRecord.objects.filter(course_record=course_record_id)
            score_choices = StudyRecord.score_choices
            return render(request, "score.html", locals())


    def extra_url(self):
        list_url = []
        list_url.append(url(r"record_socre/(\d+)", self.score))

        return list_url


    def record(self, obj=None, is_header=False):
        """
        记录考勤的自定义字段
        :param obj:
        :param is_header:
        :return:
        """
        if is_header:
            return "考勤"

        return mark_safe("<a href='/Xadmin/crm/studyrecord/?course_record={}'>记录</a>".format(obj.pk))

    def record_score(self, obj=None, is_header=False):
        if is_header:
            return "录入成绩"
        return mark_safe("<a href='record_socre/{}'>录入成绩</a>".format(obj.pk))

    list_display = ["class_obj", "day_num", "teacher", record, record_score]

    def patch_studyrecord(self, request, queryset):
        # print(queryset)
        list_studyrecord = []
        for course_record in queryset:
            # 取到与course_record相关的全部学生
            student_list = Student.objects.filter(class_list__id=course_record.class_obj.pk)
            # print(student_list)
            # 对每个学生创建学习记录对象
            for student in student_list:
                obj_studyrecord = StudyRecord(student=student, course_record=course_record)
                list_studyrecord.append(obj_studyrecord)
        # print(list_studyrecord)

        # 批量添加学习记录
        StudyRecord.objects.bulk_create(list_studyrecord)

    patch_studyrecord.short_description = "批量生成学习记录"
    actions = [patch_studyrecord, ]



site.register(CourseRecord, CourseRecordConfig)


class StudyRecordConfig(ModelXadmin):
    list_display = ["course_record", "student", "record", "score", "homework_note"]

    def patch_late(self, request, queryset):
        queryset.update(record="late")

    patch_late.short_description = "迟到"
    actions = [patch_late, ]


site.register(StudyRecord, StudyRecordConfig)
