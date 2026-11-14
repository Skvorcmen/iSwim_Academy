from django.conf import settings


def site_contacts(request):
    return {
        "SITE": {
            "phone": settings.CONTACT_PHONE,
            "email": settings.CONTACT_EMAIL,
            "instagram": settings.SOCIAL_INSTAGRAM,
            "whatsapp": settings.SOCIAL_WHATSAPP,
            "youtube": settings.SOCIAL_YOUTUBE,
            "clients": settings.CLIENTS_COUNT,
        }
    }
