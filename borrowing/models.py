from django.db import models
from django.conf import settings
from books.models import Book

class BorrowRecord(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]

    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='borrow_records')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    renewed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.member} - {self.book.title}"

class Fine(models.Model):
    borrow_record = models.OneToOneField(BorrowRecord, on_delete=models.CASCADE, related_name='fine')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    is_waived = models.BooleanField(default=False)

    def __str__(self):
        return f"Fine for {self.borrow_record}"

class Reservation(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    reserved_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.member} reserved {self.book.title}"
