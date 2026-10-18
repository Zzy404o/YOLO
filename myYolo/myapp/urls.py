from django.urls import path
from myapp import views,code

urlpatterns = [
    path('task/list/',views.TaskViewSet.as_view(
        {'get':'list','post':'create'}
    )),
    path('task/set/<int:pk>/',views.TaskViewSet.as_view(
        {"get":"retrieve","put":"update","patch":"partial_update","delete":"destroy"}
    )),
    path('user/info/',views.UserInfo.as_view()),

    path('image/code/',code.image_code),

    path('login/',views.Login.as_view()),

    path('commit/list/',views.CommitTask.as_view()),
    path('commit/set/<int:pk>/',views.CommitDetail.as_view()),

    path('user/task/',views.TaskList.as_view()),
]