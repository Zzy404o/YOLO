from rest_framework import serializers
from myapp.models import Task
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