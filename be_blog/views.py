# be_blog/views.py

from django.http import JsonResponse


def health_check(request):
    """
    Endpoint i thjeshte per health-check (p.sh. UptimeRobot, Render).
    Nuk prek databazen qellimisht - vetem konfirmon qe procesi eshte gjalle,
    keshtu qe pergjigjet shpejt dhe nuk shton ngarkese te panevojshme.
    """
    return JsonResponse({"status": "ok"})