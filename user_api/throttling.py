# Throttle-e te dedikuara per endpoint-et publike te autentikimit —
# pa kufizim keto ishin te hapura per sulme brute-force fjalekalimesh.
# Rates konfigurohen ne be_blog/settings.py -> REST_FRAMEWORK -> DEFAULT_THROTTLE_RATES.

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'


class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'


class ModeratorLoginRateThrottle(AnonRateThrottle):
    scope = 'moderator_login'
