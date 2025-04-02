from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, VerifyEmailView, LoginInitiateView, LoginCompleteView,
    RequestPasswordResetView, ResetPasswordView, UserInfoView,
    ResendOTPView
)
from .views import test

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('login/initiate/', LoginInitiateView.as_view(), name='login-initiate'),
    path('login/complete/', LoginCompleteView.as_view(), name='login-complete'),
    path('password/reset/request/', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('password/reset/complete/', ResetPasswordView.as_view(), name='reset-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('user/info/', UserInfoView.as_view(), name='user-info'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('logout/', LogoutView.as_view(), name='logout'),
]