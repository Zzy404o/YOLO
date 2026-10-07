from django.urls import path
from myapp import views

urlpatterns = [
    path('task/list/',views.TaskViewSet.as_view(
        {'get':'list','post':'create'}
    )),
    path('task/set/<int:pk>/',views.TaskViewSet.as_view(
        {"get":"retrieve","put":"update","patch":"partial_update","delete":"destroy"}
    )),
]