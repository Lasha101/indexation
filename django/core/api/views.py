from django.shortcuts import render
from .models import Person

def index(request):
    context = {}
    if request.method == "POST":
        name = request.POST.get("name")

        person = Person.objects.create(name=name.strip())

        context["name"] = person.name

    return render(request, "api/index.html", context)