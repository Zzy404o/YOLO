from rest_framework import viewsets
from myapp.models import Task
from myapp.serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)