from rest_framework import viewsets,status,generics
from rest_framework.views import APIView

from myapp.models import Task,Commit
from django.contrib.auth.models import User
from myapp.serializers import TaskSerializer, LoginSerializer,CommitSerializer
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication,TokenAuthentication
from django.contrib import auth

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import zipfile

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
        if target_status == 2:
            if instance.status != 1:
                return Response({"msg": "任务已被领取，无法重复领取"}, status=status.HTTP_400_BAD_REQUEST)
            instance.person = self.request.user
        elif target_status == 1:
            if instance.status == 3:
                return Response({"msg":"任务已提交,无法归还"},status=status.HTTP_400_BAD_REQUEST)
            instance.person = None
        elif target_status == 3:
            if instance.status == 1:
                return Response({"msg":"任务提交需要先领取"},status=status.HTTP_400_BAD_REQUEST)
            if instance.status == 2 and instance.person != self.request.user:
                return Response({"msg":"任务已被领取"},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"msg":"状态不存在"},status=status.HTTP_400_BAD_REQUEST)
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