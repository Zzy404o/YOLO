from rest_framework import serializers
from myapp.models import Task,Commit
from django.contrib.auth.models import User

class TaskSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.username')
    person = serializers.SerializerMethodField()

    def get_person(self, obj):
        if obj.person:
            return obj.person.username
        return None

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ["creator", "create_time", "num"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    pwd = serializers.CharField()
    code = serializers.CharField()

class CommitSerializer(serializers.ModelSerializer):
    task = serializers.SerializerMethodField()
    def get_task(self,obj):
        return f"{obj.task.id}-{obj.task.title}"
    commit_person = serializers.ReadOnlyField(source='commit_person.username')
    check_person = serializers.SerializerMethodField()
    def get_check_person(self,obj):
        if obj.check_person:
            return obj.check_person.username
        return None

    class Meta:
        model = Commit
        fields = '__all__'
        read_only_fields = ["task", "commit_person", "check_person"]
        extra_kwargs = {
            'commit_zip': {
                'error_messages': {
                    'invalid': '必须上传commit_zip压缩包',
                }
            }
        }