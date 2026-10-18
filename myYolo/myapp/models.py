from django.db import models
from django.conf import settings
import zipfile
from django.utils import timezone

class Task(models.Model):
    """任务表"""
    title = models.CharField(verbose_name='任务名',max_length=32)
    detail = models.TextField(verbose_name='详情')
    num = models.IntegerField(verbose_name='图片数量')
    task_file = models.FileField(verbose_name="数据集压缩包", upload_to="task_zip/")
    create_time = models.DateTimeField(auto_now_add=True,verbose_name='创建时间')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,verbose_name='创建人',related_name='created_tasks')
    status_choice = (
        (1,'未领取'),
        (2,'标注中'),
        (3,'审核中'),
        (4,'已完成')
    )
    status = models.SmallIntegerField(verbose_name='状态',choices=status_choice,default=1)
    person = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,verbose_name="标注人",blank=True,null=True,related_name='assigned_tasks')

    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务列表'
        ordering = ('-create_time','num','status')

    def save(self, *args, **kwargs):
        file_changed = False
        if self.pk is None:
            file_changed = True
        else:
            old_obj = Task.objects.get(pk=self.pk)
            file_changed = old_obj.task_file != self.task_file

        # 当上传了zip文件时
        if self.task_file and file_changed:
            with zipfile.ZipFile(self.task_file) as zf:
                count = 0
                # 遍历压缩包里所有文件
                for filename in zf.namelist():
                    # 过滤图片后缀，排除文件夹
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')) and not filename.endswith('/'):
                        count += 1
                self.num = count
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Commit(models.Model):
    """提交表"""
    task = models.ForeignKey(to=Task,on_delete=models.PROTECT,verbose_name='任务')
    txt = models.TextField(verbose_name='备注',blank=True)
    commit_time = models.DateTimeField(auto_now_add=True,verbose_name="提交时间")
    commit_zip = models.FileField(verbose_name="任务提交",upload_to="commit_zip/")
    commit_person = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,verbose_name="提交人",related_name='commit_person')
    check_choice = (
        (1,'待审核'),
        (2,'已打回'),
        (3,'审核通过')
    )
    check_status = models.SmallIntegerField(verbose_name="审核情况",choices=check_choice,default=1)
    check_txt = models.TextField(verbose_name="修改意见",blank=True,null=True)
    check_person = models.ForeignKey(settings.AUTH_USER_MODEL,null=True, blank=True,on_delete=models.PROTECT,verbose_name="审核员",related_name="check_person")
    check_time = models.DateTimeField(null=True,blank=True,verbose_name='审核时间')

    class Meta:
        verbose_name = '提交'
        verbose_name_plural = '提交列表'
        ordering = ('-commit_time','check_status')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 审核结果联动任务状态
        if self.check_status == 2:
            Task.objects.filter(id=self.task_id).update(status=2, person=self.commit_person)
        elif self.check_status == 3:
            Task.objects.filter(id=self.task_id).update(status=4)

    def __str__(self):
        return self.task.title

class Back(models.Model):
    """归还表"""
    back_user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,verbose_name="归还人")
    back_task = models.ForeignKey(to=Task,on_delete=models.CASCADE,verbose_name="归还任务")
    back_time = models.DateTimeField(auto_now_add=True,verbose_name="归还时间")
    back_round = models.IntegerField(verbose_name="归还次数",default=0)

    class Meta:
        verbose_name = '归还'
        verbose_name_plural = '归还领取限制'

    def interval_time(self):
        interval = timezone.now() - self.back_time
        return interval
