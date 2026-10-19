from rest_framework import viewsets,status,generics
from rest_framework.views import APIView

from myapp.models import Task,Commit,Back,UserTask
from django.contrib.auth.models import User
from myapp.serializers import TaskSerializer, LoginSerializer,CommitSerializer,UserTaskSerializer
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication,TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib import auth

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import zipfile
from django.db.models import F
from django.utils import timezone
from datetime import timedelta

from rest_framework.decorators import api_view

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

class TaskViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, CsrfExemptSessionAuthentication)
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        target_status = request.data.get("status")
        if target_status == 1:
            if instance.status == 3 or instance.status == 4:
                return Response({"msg":"任务已提交,无法归还"},status=status.HTTP_400_BAD_REQUEST)
            Back.objects.create(back_user=self.request.user, back_task=instance)
            Back.objects.filter(back_user=self.request.user).update(back_round=F('back_round')+1)
            instance.person = None
        elif target_status == 2:
            one_week_ago = timezone.now() - timedelta(days=7)
            back_count = Back.objects.filter(back_user=self.request.user,back_time__gte=one_week_ago).order_by("back_time").first()
            if back_count:
                back_round = back_count.back_round
                if back_round >=10:
                    return Response({'msg':"近一周归还次数过多，暂时禁止领取任务"},status.HTTP_400_BAD_REQUEST)
            if instance.status != 1:
                return Response({"msg": "任务已被领取，无法重复领取"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                back_list = Back.objects.filter(back_user=self.request.user)
                for back in back_list:
                    if back.back_task.id == instance.id:
                        interval = back.interval_time()
                        if interval.total_seconds() >= 24*60*60:
                            continue
                        else:
                            return Response({"msg":"该任务24小时不得领取"},status=status.HTTP_400_BAD_REQUEST)
                # 检查和写入在同一条 SQL 里，多个用户同时领取只有一个能成功
                updated = Task.objects.filter(pk=instance.pk, status=1).update(status=2, person=self.request.user)
                if updated == 0:
                    return Response({"msg": "任务已被领取，无法重复领取"}, status=status.HTTP_400_BAD_REQUEST)
                instance.refresh_from_db()
                serializer = self.get_serializer(instance)
                return Response(serializer.data)
        elif target_status == 3:
            if instance.status == 1:
                return Response({"msg":"任务提交需要先领取"},status=status.HTTP_400_BAD_REQUEST)
            if instance.status == 2 and instance.person != self.request.user:
                return Response({"msg":"任务已被领取"},status=status.HTTP_400_BAD_REQUEST)
            if instance.status == 4:
                return Response({"msg":"任务已完成"},status=status.HTTP_400_BAD_REQUEST)
        elif target_status == 4:
            if instance.status == 1:
                return Response({'msg':'未领取任务'},status=status.HTTP_400_BAD_REQUEST)
            if instance.status == 2 and instance.person != self.request.user:
                return Response({'msg':'任务已被领取'},status=status.HTTP_400_BAD_REQUEST)
            if instance.status == 2 and instance.person == self.request.user:
                return Response({'msg':'需要提交任务'},status=status.HTTP_400_BAD_REQUEST)
            if instance.status == 3:
                commit_obj = Commit.objects.filter(task=instance.id).first()
                if commit_obj:
                    commit_status = commit_obj.check_status
                else:
                    commit_status = 4
                if commit_status == 1:
                    return Response({'msg':"任务待审核"},status=status.HTTP_400_BAD_REQUEST)
                if commit_status == 2:
                    return Response({'msg':'任务需要修改'},status=status.HTTP_400_BAD_REQUEST)
                if commit_status == 4:
                    return Response({'msg': '任务不存在'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"msg":"你干嘛哎呦"},status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

class UserInfo(APIView):
    def get(self,request):
        info = request.session.get('info')
        if not info:
            return Response({'status': 0, 'msg': '未登录'})
        return Response({'status': 200, 'data': info})

@method_decorator(csrf_exempt,name='post')
class Login(APIView):
    authentication_classes = []
    def post(self,request):
        s = LoginSerializer(data=request.data)
        if s.is_valid():
            input_code = s.validated_data.get('code')
            code = request.session.get('check_code','')
            if input_code != code:
                return Response({'status':4,'error':'验证码错误'})
            del request.session['check_code']
            input_name = s.validated_data.get('username')
            input_pwd = s.validated_data.get('pwd')
            user = User.objects.filter(username=input_name).first()
            if user:
                result = user.check_password(input_pwd)
                if not result:
                    return Response({'status':5,'error':'用户名或密码错误'})

                auth.login(request, user)
                request.session['info'] = {
                    'id': user.id,
                    'username':user.username,
                }

                request.session.set_expiry(60*60*24*7)
                return Response({'status':6})
            return Response({'status': 5, 'error': '用户名或密码错误'})
        return Response({"status": 1, "error": s.errors})


class CommitTask(APIView):
    authentication_classes = (TokenAuthentication, CsrfExemptSessionAuthentication)
    def get(self,request):
        queryset = Commit.objects.all()
        s = CommitSerializer(instance=queryset,many=True)
        return Response(s.data, status=status.HTTP_200_OK)
    def post(self,request):
        s = CommitSerializer(data=request.data)
        if s.is_valid():
            input_zip = s.validated_data.get("commit_zip")
            task_id = request.data.get("task")
            obj = Task.objects.filter(id=task_id).first()
            if not obj:
                return Response({"error": "任务不存在"})
            # 只能给自己领取的任务提交
            if obj.person != request.user:
                return Response({"error": "只有本人领取的任务才能提交"})
            with zipfile.ZipFile(input_zip) as cf:
                count = 0
                for filename in cf.namelist():
                    if filename.lower().endswith('.txt') and not filename.endswith('/'):
                        count += 1
                if count != obj.num:
                    return Response({'error': "文件数量错误"})
            s.save(task=obj,commit_person=self.request.user)
            return Response({"msg": "提交成功"}, status=status.HTTP_201_CREATED)
        return Response({"error": s.errors})


class CommitDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Commit.objects.all()
    serializer_class = CommitSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.check_status == 2:
            return Response({"msg": "该提交记录已打回，不可重复修改审核状态"}, status=status.HTTP_400_BAD_REQUEST)

        send_status = request.data.get("check_status")
        if send_status == 1:
            instance.check_person = None

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

class TaskList(APIView):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        queryset = UserTask.objects.filter(commit_user=request.user).order_by("-change_time")
        # 每个任务取最新一条审核的状态：最新仍是不合格的任务才算待修改
        # 任务后来通过审核的话，早先的不合格记录不再置顶
        latest = {}
        for r in queryset:
            latest.setdefault(r.change_task_id, r.change_status)
        s = UserTaskSerializer(instance=queryset, many=True)
        data = s.data
        for item, r in zip(data, queryset):
            item["is_pending"] = (latest[r.change_task_id] == 1)
        return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
def logout(request):
    request.session.clear()
    return Response({'msg':"已退出"},status=status.HTTP_200_OK)