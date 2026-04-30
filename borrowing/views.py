from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import date, timedelta
from django.db.models import Sum

from accounts.models import User
from books.models import Book
from .models import BorrowRecord, Fine, Reservation
from .serializers import BorrowRecordSerializer, FineSerializer

class IsLibrarianOrAdminPermission(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.role in ['librarian', 'admin']

class IssueBookView(APIView):
    permission_classes = [IsLibrarianOrAdminPermission]

    def post(self, request):
        member_id = request.data.get('member_id')
        book_id = request.data.get('book_id')

        if not member_id or not book_id:
            return Response({
                "success": False,
                "message": "member_id and book_id are required",
                "errors": {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = User.objects.get(id=member_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": {"member_id": ["Member does not exist."]}
            }, status=status.HTTP_404_NOT_FOUND)
        
        if member.is_suspended:
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": {"member": ["Member is suspended."]}
            }, status=status.HTTP_400_BAD_REQUEST)

        if member.membership_expiry and member.membership_expiry < date.today():
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": {"member": ["Membership has expired."]}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": {"book_id": ["Book does not exist."]}
            }, status=status.HTTP_404_NOT_FOUND)

        if book.available_copies <= 0:
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": {"book": ["No available copies for this book."]}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check unpaid fines > $5
        unpaid_fines = Fine.objects.filter(
            borrow_record__member=member,
            is_paid=False,
            is_waived=False
        ).aggregate(total=Sum('amount'))['total'] or 0

        if unpaid_fines > 5:
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": {"member": [f"Member has unpaid fines exceeding $5.00 (Total: ${unpaid_fines})."]}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create BorrowRecord
        borrow_record = BorrowRecord.objects.create(
            member=member,
            book=book,
            due_date=date.today() + timedelta(days=14)
        )

        book.available_copies -= 1
        book.save()

        serializer = BorrowRecordSerializer(borrow_record)

        return Response({
            "success": True,
            "message": "Book issued successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class ReturnBookView(APIView):
    permission_classes = [IsLibrarianOrAdminPermission]

    def post(self, request):
        borrow_id = request.data.get('borrow_id')

        if not borrow_id:
            return Response({
                "success": False,
                "message": "borrow_id is required",
                "errors": {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            borrow_record = BorrowRecord.objects.get(id=borrow_id)
        except BorrowRecord.DoesNotExist:
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": {"borrow_id": ["Borrow record does not exist."]}
            }, status=status.HTTP_404_NOT_FOUND)

        if borrow_record.status == 'returned':
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": {"borrow_id": ["Book is already returned."]}
            }, status=status.HTTP_400_BAD_REQUEST)

        today = date.today()
        borrow_record.return_date = today
        borrow_record.status = 'returned'
        borrow_record.save()

        book = borrow_record.book
        book.available_copies += 1
        book.save()

        fine_data = None
        if today > borrow_record.due_date:
            overdue_days = (today - borrow_record.due_date).days
            amount = overdue_days * 0.50
            fine = Fine.objects.create(
                borrow_record=borrow_record,
                amount=amount
            )
            fine_data = FineSerializer(fine).data

        # Check Reservations
        active_reservation = Reservation.objects.filter(
            book=book,
            is_active=True,
            expires_at__isnull=True
        ).order_by('reserved_at').first()

        if active_reservation:
            active_reservation.expires_at = today + timedelta(days=3)
            active_reservation.save()

        serializer = BorrowRecordSerializer(borrow_record)
        response_data = serializer.data
        if fine_data:
            response_data['fine'] = fine_data

        return Response({
            "success": True,
            "message": "Book returned successfully",
            "data": response_data
        }, status=status.HTTP_200_OK)
