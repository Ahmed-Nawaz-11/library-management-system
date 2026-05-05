from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticates requests using an access token stored in an HTTP-only cookie.
    Falls back to the Authorization header so Postman / API clients still work.
    """

    def authenticate(self, request):
        # 1. Try the standard Authorization header first (Postman / non-browser clients)
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            # 2. Fall back to the HTTP-only cookie set by LoginView
            cookie_token = request.COOKIES.get('access_token')
            if cookie_token is None:
                return None
            raw_token = cookie_token.encode('utf-8')

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError):
            return None
