from django.contrib import admin
from myapp.models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # 显示的字段
    list_display = ('title','num', 'create_time', 'creator')
    # 可以搜索的字段
    search_fields = ('title', 'detail','creator__username')
    # 过滤的字段
    list_filter = ('creator', 'create_time')
    # 创建时填写的字段
    fields = ('title', 'detail', 'task_file', 'creator')
    readonly_fields = ('num',)
