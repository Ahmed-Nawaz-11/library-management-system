from rest_framework.views import APIView
from rest_framework.response import Response
from library_management_system.utils import success_response, error_response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import date, timedelta
from django.db.models import Sum, Count

from accounts.models import User
from books.models import Book
from .models import BorrowRecord, Fine, Reservation
from .serializers import BorrowRecordSerializer, FineSerializer, ReservationSerializer

from library_management_system.permissions import IsAdmin, IsLibrarian, IsAdminOrLibrarian, IsMember, IsOwnerOrAdminOrLibrarian

class IssueBookView(APIView):
    permission_classes = [IsAdminOrLibrarian]

    def post(self, request):
        member_id = request.data.get('member_id')
        book_id = request.data.get('book_id')

        if not member_id or not book_id:
            return error_response(message="member_id and book_id are required", errors={}, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = User.objects.get(id=member_id)
        except User.DoesNotExist:
            return error_response(message="Validation failed", errors={"member_id": ["Member does not exist."]}, status=status.HTTP_404_NOT_FOUND)
        
        if member.is_suspended:
            return error_response(message="Validation failed", errors={"member": ["Member is suspended."]}, status=status.HTTP_400_BAD_REQUEST)

        if member.membership_expiry and member.membership_expiry < date.today():
            return error_response(message="Validation failed", errors={"member": ["Membership has expired."]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return error_response(message="Validation failed", errors={"book_id": ["Book does not exist."]}, status=status.HTTP_404_NOT_FOUND)

        if book.available_copies <= 0:
            return error_response(message="Validation failed", errors={"book": ["No available copies for this book."]}, status=status.HTTP_400_BAD_REQUEST)

        # Check unpaid fines > $5
        unpaid_fines = Fine.objects.filter(
            borrow_record__member=member,
            is_paid=False,
            is_waived=False
        ).aggregate(total=Sum('amount'))['total'] or 0

        if unpaid_fines > 5:
            return error_response(message="Validation failed", errors={"member": [f"Member has unpaid fines exceeding $5.00 (Total: ${unpaid_fines})."]}, status=status.HTTP_400_BAD_REQUEST)

        # Create BorrowRecord
        borrow_record = BorrowRecord.objects.create(
            member=member,
            book=book,
            due_date=date.today() + timedelta(days=14)
        )

        book.available_copies -= 1
        book.save()

        serializer = BorrowRecordSerializer(borrow_record)

        return success_response(data=serializer.data, message="Book issued successfully", status=status.HTTP_201_CREATED)


class ReturnBookView(APIView):
    permission_classes = [IsAdminOrLibrarian]

    def post(self, request):
        borrow_id = request.data.get('borrow_id')

        if not borrow_id:
            return error_response(message="borrow_id is required", errors={}, status=status.HTTP_400_BAD_REQUEST)

        try:
            borrow_record = BorrowRecord.objects.get(id=borrow_id)
        except BorrowRecord.DoesNotExist:
            return error_response(message="Validation failed", errors={"borrow_id": ["Borrow record does not exist."]}, status=status.HTTP_404_NOT_FOUND)

        if borrow_record.status == 'returned':
            return error_response(message="Validation failed", errors={"borrow_id": ["Book is already returned."]}, status=status.HTTP_400_BAD_REQUEST)

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

        return success_response(data=response_data, message="Book returned successfully", status=status.HTTP_200_OK)

class BorrowHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'member':
            records = BorrowRecord.objects.filter(member=request.user).order_by('-borrow_date')
        else:
            member_id = request.query_params.get('member_id')
            if member_id:
                records = BorrowRecord.objects.filter(member_id=member_id).order_by('-borrow_date')
            else:
                records = BorrowRecord.objects.all().order_by('-borrow_date')

        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_records = paginator.paginate_queryset(records, request)

        serializer = BorrowRecordSerializer(paginated_records, many=True)
        data = []
        for index, record in enumerate(paginated_records):
            record_data = serializer.data[index]
            try:
                fine = record.fine
                record_data['fine_amount'] = str(fine.amount) if not fine.is_paid and not fine.is_waived else "0.00"
            except Exception:
                pass
            data.append(record_data)

        return success_response(
            data=data,
            message="Borrow history retrieved successfully",
            pagination={
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "current_page": paginator.page.number,
                "total_pages": paginator.page.paginator.num_pages
            }
        )

class RenewBookView(APIView):
    permission_classes = [IsAdminOrLibrarian]

    def post(self, request):
        borrow_id = request.data.get('borrow_id')

        if not borrow_id:
            return error_response(message="borrow_id is required", errors={}, status=status.HTTP_400_BAD_REQUEST)

        try:
            borrow_record = BorrowRecord.objects.get(id=borrow_id)
        except BorrowRecord.DoesNotExist:
            return error_response(message="Validation failed", errors={"borrow_id": ["Borrow record does not exist."]}, status=status.HTTP_404_NOT_FOUND)

        # Permission checked via IsAdminOrLibrarian class

        if borrow_record.status != 'borrowed':
            return error_response(message="Validation failed", errors={"borrow_id": ["Book is not currently borrowed."]}, status=status.HTTP_400_BAD_REQUEST)

        if borrow_record.renewed:
            return error_response(message="Validation failed", errors={"borrow_id": ["Book has already been renewed once."]}, status=status.HTTP_400_BAD_REQUEST)

        active_reservation = Reservation.objects.filter(
            book=borrow_record.book,
            is_active=True,
            expires_at__isnull=True
        ).exclude(member=borrow_record.member).exists()

        if active_reservation:
            return error_response(message="Validation failed", errors={"book": ["Cannot renew, book is reserved by another member."]}, status=status.HTTP_400_BAD_REQUEST)

        borrow_record.due_date = borrow_record.due_date + timedelta(days=14)
        borrow_record.renewed = True
        borrow_record.save()

        serializer = BorrowRecordSerializer(borrow_record)
        return success_response(data=serializer.data, message="Book renewed successfully", status=status.HTTP_200_OK)

class OverdueBooksView(APIView):
    permission_classes = [IsAdminOrLibrarian]

    def get(self, request):
        today = date.today()
        overdue_records = BorrowRecord.objects.filter(status='borrowed', due_date__lt=today)
        for record in overdue_records:
            record.status = 'overdue'
            record.save()

        records = BorrowRecord.objects.filter(status='overdue').order_by('due_date')

        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_records = paginator.paginate_queryset(records, request)

        serializer = BorrowRecordSerializer(paginated_records, many=True)
        data = []
        for index, record in enumerate(paginated_records):
            record_data = serializer.data[index]
            record_data['days_overdue'] = (today - record.due_date).days
            data.append(record_data)

        return success_response(
            data=data,
            message="Overdue books retrieved successfully",
            pagination={
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "current_page": paginator.page.number,
                "total_pages": paginator.page.paginator.num_pages
            }
        )

class ReservationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'member':
            reservations = Reservation.objects.filter(member=request.user, is_active=True).order_by('-reserved_at')
        else:
            reservations = Reservation.objects.all().order_by('-reserved_at')

        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_reservations = paginator.paginate_queryset(reservations, request)

        serializer = ReservationSerializer(paginated_reservations, many=True)
        return success_response(data=serializer.data, message="Reservations retrieved successfully", pagination={"count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "current_page": paginator.page.number,
                "total_pages": paginator.page.paginator.num_pages})

    def post(self, request):
        book_id = request.data.get('book_id')
        if not book_id:
            return error_response(message="book_id is required", errors={}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return error_response(message="Validation failed", errors={"book_id": ["Book does not exist."]}, status=status.HTTP_404_NOT_FOUND)

        if book.available_copies > 0:
            return error_response(message="Validation failed", errors={"book": ["Book is currently available. Please borrow it directly."]}, status=status.HTTP_400_BAD_REQUEST)

        existing_reservation = Reservation.objects.filter(
            member=request.user,
            book=book,
            is_active=True
        ).exists()

        if existing_reservation:
            return error_response(message="Validation failed", errors={"book": ["You already have an active reservation for this book."]}, status=status.HTTP_400_BAD_REQUEST)

        reservation = Reservation.objects.create(
            member=request.user,
            book=book
        )

        serializer = ReservationSerializer(reservation)
        return success_response(data=serializer.data, message="Reservation created successfully", status=status.HTTP_201_CREATED)

class CancelReservationView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        try:
            reservation = Reservation.objects.get(id=id)
        except Reservation.DoesNotExist:
            return error_response(message="Reservation does not exist", errors={}, status=status.HTTP_404_NOT_FOUND)

        if reservation.member != request.user:
            return error_response(message="You can only cancel your own reservations.", errors={}, status=status.HTTP_403_FORBIDDEN)

        if not reservation.is_active:
            return error_response(message="Reservation is already inactive.", errors={}, status=status.HTTP_400_BAD_REQUEST)

        reservation.is_active = False
        reservation.save()

        return success_response(data={}, message="Reservation cancelled successfully", status=status.HTTP_200_OK)

class FineListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'member':
            fines = Fine.objects.filter(borrow_record__member=request.user).order_by('-id')
        else:
            is_paid = request.query_params.get('is_paid')
            if is_paid is not None:
                is_paid_bool = is_paid.lower() == 'true'
                fines = Fine.objects.filter(is_paid=is_paid_bool).order_by('-id')
            else:
                fines = Fine.objects.all().order_by('-id')

        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_fines = paginator.paginate_queryset(fines, request)

        serializer = FineSerializer(paginated_fines, many=True)
        return success_response(
            data=serializer.data,
            message="Fines retrieved successfully",
            pagination={
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "current_page": paginator.page.number,
                "total_pages": paginator.page.paginator.num_pages
            }
        )

class PayFineView(APIView):
    permission_classes = [IsAdminOrLibrarian]

    def post(self, request, id):
        try:
            fine = Fine.objects.get(id=id)
        except Fine.DoesNotExist:
            return error_response(message="Fine does not exist", errors={}, status=status.HTTP_404_NOT_FOUND)

        if fine.is_paid or fine.is_waived:
            return error_response(message="Fine is already paid or waived.", errors={}, status=status.HTTP_400_BAD_REQUEST)

        fine.is_paid = True
        fine.save()

        serializer = FineSerializer(fine)
        return success_response(data=serializer.data, message="Fine marked as paid successfully", status=status.HTTP_200_OK)

class WaiveFineView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, id):
        # Permission checked via IsAdmin class

        try:
            fine = Fine.objects.get(id=id)
        except Fine.DoesNotExist:
            return error_response(message="Fine does not exist", errors={}, status=status.HTTP_404_NOT_FOUND)

        if fine.is_paid or fine.is_waived:
            return error_response(message="Fine is already processed.", errors={}, status=status.HTTP_400_BAD_REQUEST)

        fine.is_waived = True
        fine.is_paid = True
        fine.amount = 0
        fine.save()

        serializer = FineSerializer(fine)
        return success_response(data=serializer.data, message="Fine waived successfully", status=status.HTTP_200_OK)

class DashboardSummaryView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        total_books = Book.objects.count()
        total_members = User.objects.filter(role='member').count()
        active_borrows = BorrowRecord.objects.filter(status='borrowed').count()
        overdue_count = BorrowRecord.objects.filter(status='borrowed', due_date__lt=today).count()
        
        total_fines_unpaid = Fine.objects.filter(is_paid=False, is_waived=False).aggregate(total=Sum('amount'))['total'] or 0.00
        
        new_members_this_month = User.objects.filter(
            role='member',
            date_joined__year=current_year,
            date_joined__month=current_month
        ).count()

        data = {
            "total_books": total_books,
            "total_members": total_members,
            "active_borrows": active_borrows,
            "overdue_count": overdue_count,
            "total_fines_unpaid": float(total_fines_unpaid),
            "new_members_this_month": new_members_this_month
        }

        return success_response(data=data, message="Dashboard summary retrieved successfully", status=status.HTTP_200_OK)

class PopularBooksView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        popular_books = Book.objects.annotate(
            borrow_count=Count('borrow_records')
        ).order_by('-borrow_count')[:10]

        data = []
        for book in popular_books:
            data.append({
                "id": book.id,
                "title": book.title,
                "author": book.author.name if hasattr(book, 'author') and book.author else None,
                "borrow_count": book.borrow_count
            })

        return success_response(data=data, message="Popular books retrieved successfully", status=status.HTTP_200_OK)

class OverdueMembersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = date.today()
        overdue_records = BorrowRecord.objects.filter(status__in=['borrowed', 'overdue'], due_date__lt=today).select_related('member', 'book')
        
        data = []
        for record in overdue_records:
            fine_amount = 0.00
            try:
                fine = record.fine
                if not fine.is_paid and not fine.is_waived:
                    fine_amount = fine.amount
            except Exception:
                pass
                
            data.append({
                "member_name": record.member.username,
                "email": record.member.email,
                "book_title": record.book.title,
                "days_overdue": (today - record.due_date).days,
                "fine_amount": str(fine_amount)
            })

        return success_response(data=data, message="Overdue members retrieved successfully", status=status.HTTP_200_OK)
