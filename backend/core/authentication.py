from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import UserSessionToken


class DeviceTokenAuthentication(BaseAuthentication):
    keyword = b"token"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth:
            return None

        if auth[0].lower() != self.keyword:
            return None

        if len(auth) != 2:
            raise AuthenticationFailed("Authorization header invalido.")

        token_key = auth[1].decode("utf-8", errors="ignore").strip()
        if not token_key:
            raise AuthenticationFailed("Token invalido.")

        try:
            session = UserSessionToken.objects.select_related("user").get(
                key=token_key,
                is_active=True,
            )
        except UserSessionToken.DoesNotExist as exc:
            raise AuthenticationFailed("Token invalido o expirado.") from exc

        if not session.user.is_active:
            raise AuthenticationFailed("Cuenta inactiva.")

        session.last_used_at = timezone.now()
        session.save(update_fields=["last_used_at"])
        return (session.user, session)
