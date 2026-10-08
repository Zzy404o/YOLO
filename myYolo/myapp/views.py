from rest_framework import viewsets,status
from rest_framework.views import APIView

from myapp.models import Task
from myapp.serializers import TaskSerializer
from rest_framework.response import Response

class TaskViewSet(viewsets.ModelViewSet):
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
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

class UserInfo(APIView):
    def get(self,request):
        return Response({"id":request.user.id,"username": request.user.username})