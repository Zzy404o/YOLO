from rest_framework import viewsets,status
from rest_framework.views import APIView

from myapp.models import Task
from django.contrib.auth.models import User
from myapp.serializers import TaskSerializer, LoginSerializer
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication,TokenAuthentication
from django.contrib import auth

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class TaskViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,SessionAuthentication)
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


