from rest_framework import serializers

class RouteRequestSerializer(serializers.Serializer):
    start = serializers.CharField(required=True, allow_blank=False, max_length=255)
    finish = serializers.CharField(required=True, allow_blank=False, max_length=255)

    def validate_start(self, value):
        if not value.strip():
            raise serializers.ValidationError("Start location cannot be empty.")
        return value.strip()

    def validate_finish(self, value):
        if not value.strip():
            raise serializers.ValidationError("Finish location cannot be empty.")
        return value.strip()
