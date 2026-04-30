from rest_framework import serializers
from .models import BorrowRecord, Fine, Reservation

class BorrowRecordSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    member_username = serializers.CharField(source='member.username', read_only=True)

    class Meta:
        model = BorrowRecord
        fields = '__all__'

class FineSerializer(serializers.ModelSerializer):
    borrow_record_id = serializers.IntegerField(source='borrow_record.id', read_only=True)

    class Meta:
        model = Fine
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    member_username = serializers.CharField(source='member.username', read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'
