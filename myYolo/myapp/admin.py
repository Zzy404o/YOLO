from django.contrib import admin
from myapp.models import Task,Commit

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # 显示的字段
    list_display = ('title','num', 'create_time', 'creator','status','person')
    # 可以搜索的字段
    search_fields = ('title', 'detail','creator__username')
    # 过滤的字段
    list_filter = ('creator', 'create_time','status','person')
    # 创建时填写的字段
    fields = ('title', 'detail', 'task_file', 'creator')
    readonly_fields = ('num','status','person')

@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ('task','txt','commit_zip','commit_person','commit_time','check_status')
    search_fields = ("task__title",'commit_time',)
    list_filter = ('commit_time','check_status')
    readonly_fields = ["commit_person", "commit_time"]