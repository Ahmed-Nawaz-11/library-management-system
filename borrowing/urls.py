from django.urls import path
from .views import (
    IssueBookView, ReturnBookView, 
    BorrowHistoryView, RenewBookView, OverdueBooksView,
    ReservationListCreateView, CancelReservationView,
    FineListView, PayFineView, WaiveFineView,
    DashboardSummaryView, PopularBooksView, OverdueMembersView
)

urlpatterns = [
    path('borrow/issue/', IssueBookView.as_view(), name='issue-book'),
    path('borrow/return/', ReturnBookView.as_view(), name='return-book'),
    path('borrow/history/', BorrowHistoryView.as_view(), name='borrow-history'),
    path('borrow/renew/', RenewBookView.as_view(), name='renew-book'),
    path('borrow/overdue/', OverdueBooksView.as_view(), name='overdue-books'),
    path('reservations/', ReservationListCreateView.as_view(), name='reservations-list-create'),
    path('reservations/<int:id>/cancel/', CancelReservationView.as_view(), name='cancel-reservation'),
    path('fines/', FineListView.as_view(), name='fines-list'),
    path('fines/<int:id>/pay/', PayFineView.as_view(), name='pay-fine'),
    path('fines/<int:id>/waive/', WaiveFineView.as_view(), name='waive-fine'),
    path('reports/summary/', DashboardSummaryView.as_view(), name='reports-summary'),
    path('reports/popular-books/', PopularBooksView.as_view(), name='reports-popular-books'),
    path('reports/overdue-members/', OverdueMembersView.as_view(), name='reports-overdue-members'),
]
