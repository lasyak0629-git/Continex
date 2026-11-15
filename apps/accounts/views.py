from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import SignupForm
from django.utils.http import url_has_allowed_host_and_scheme

def signup(request):
    if request.user.is_authenticated:

        nxt = request.GET.get("next", "")
        ok = url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()})
        # ... then at each redirect:
        return redirect(nxt if ok else "home")
    
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)

        nxt = request.GET.get("next", "")
        ok = url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()})
        # ... then at each redirect:
        return redirect(nxt if ok else "home")
    
    return render(request, "signup.html", {"form": form})