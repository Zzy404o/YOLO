from django.db import models
from django.conf import settings
import zipfile

class Task(models.Model):
    """任务表"""
    title = models.CharField(verbose_name='任务名',max_length=32)
    detail = models.TextField(verbose_name='详情')
    num = models.IntegerField(verbose_name='图片数量')
    task_file = models.FileField(verbose_name="数据集压缩包", upload_to="task_zip/")
    create_time = models.DateTimeField(auto_now_add=True,verbose_name='创建时间')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,verbose_name='创建人')
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务列表'
        ordering = ('-create_time','num')

    def save(self, *args, **kwargs):
        # 当上传了zip文件时
        if self.task_file:
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