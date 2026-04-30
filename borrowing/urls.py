from django.urls import path
from .views import IssueBookView, ReturnBookView

urlpatterns = [
    path('borrow/issue/', IssueBookView.as_view(), name='issue-book'),
    path('borrow/return/', ReturnBookView.as_view(), name='return-book'),
]
