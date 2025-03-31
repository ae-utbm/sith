from django.shortcuts import render


def april_fool(request):
    return render(request, "april/age_confirm.jinja")


def april_fool_sli(request):
    return render(request, "april/sli.jinja")
