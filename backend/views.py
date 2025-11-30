from django.http import HttpResponse
import os

def frontend(request):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "frontend", "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HttpResponse(f.read())
