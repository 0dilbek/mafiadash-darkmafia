import logging
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .cinema_forms import CinemaMovieForm, CinemaPlanForm
from .cinema_models import (
    CinemaChannel, CinemaJoinRequest, CinemaMovie, CinemaPlan, CinemaPurchase, CinemaSubscription,
)


logger = logging.getLogger(__name__)


def cinema_admin_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return HttpResponseForbidden("Bu menyu faqat administratorlar uchun.")
        return view(request, *args, **kwargs)
    return wrapped


@cinema_admin_required
@require_http_methods(["GET", "POST"])
def cinema_dashboard(request):
    tab = request.GET.get("tab", "settings")
    if tab not in {"settings", "movies", "channels", "subscriptions", "purchases"}:
        tab = "settings"
    context = {"tab": tab, "q": request.GET.get("q", "").strip()[:100]}
    status = 200
    try:
        plan, _ = CinemaPlan.objects.get_or_create(pk=1)
        form = CinemaPlanForm(request.POST or None, instance=plan)
        if request.method == "POST":
            if form.is_valid():
                with transaction.atomic():
                    locked_plan = CinemaPlan.objects.select_for_update().get(pk=1)
                    for field in form.Meta.fields:
                        setattr(locked_plan, field, form.cleaned_data[field])
                    locked_plan.save(update_fields=[*form.Meta.fields, "updated_at"])
                messages.success(request, "Obuna shartlari saqlandi. Bot yangi xaridlarda shu qiymatlarni ishlatadi.")
                return redirect("cinema")
            tab = context["tab"] = "settings"
            status = 400
        paid = CinemaPurchase.objects.filter(paid_at__isnull=False)
        context.update({
            "form": form,
            "movie_count": CinemaMovie.objects.count(),
            "channel_count": CinemaChannel.objects.count(),
            "active_count": CinemaSubscription.objects.filter(expires_at__gt=timezone.now()).count(),
            "revenue": paid.aggregate(total=Sum("price_diamonds"))["total"] or 0,
        })
        q = context["q"]
        rows = None
        if tab == "movies":
            rows = CinemaMovie.objects.order_by("-created_at", "id")
            if q:
                rows = rows.filter(Q(code__icontains=q) | Q(message_text__icontains=q))
        elif tab == "channels":
            rows = CinemaChannel.objects.annotate(request_total=Count("join_requests")).order_by("id")
        elif tab == "subscriptions":
            rows = CinemaSubscription.objects.select_related("user", "user__profile").order_by("-expires_at")
            if q:
                rows = rows.filter(Q(user__full_name__icontains=q) | Q(user__user_id__icontains=q))
            context["now"] = timezone.now()
        elif tab == "purchases":
            rows = paid.select_related("user").order_by("-paid_at")
            if q:
                rows = rows.filter(Q(user__full_name__icontains=q) | Q(user__user_id__icontains=q))
        if rows is not None:
            context["page_obj"] = Paginator(rows, 25).get_page(request.GET.get("page"))
            # Evaluate within error handler, including the lazy page query.
            context["rows"] = list(context["page_obj"])
    except DatabaseError:
        logger.exception("Cinema jadvallarini o'qish/saqlashda xato")
        context["storage_error"] = True
        status = 503
    return render(request, "bot/cinema.html", context, status=status)


@cinema_admin_required
@require_http_methods(["GET", "POST"])
def cinema_movie(request, pk=None):
    movie = get_object_or_404(CinemaMovie, pk=pk) if pk is not None else None
    form = CinemaMovieForm(request.POST or None, instance=movie)
    if request.method == "POST" and form.is_valid():
        try:
            # Update only editable fields so a concurrent bot view-count increment is preserved.
            if movie:
                CinemaMovie.objects.filter(pk=movie.pk).update(**form.cleaned_data, updated_at=timezone.now())
            else:
                form.save()
        except IntegrityError:
            form.add_error("code", "Bu kod boshqa kino uchun band qilingan.")
        else:
            messages.success(request, "Kino saqlandi.")
            return redirect(f"{reverse('cinema')}?tab=movies")
    return render(request, "bot/cinema_movie.html", {"form": form, "movie": movie},
                  status=400 if request.method == "POST" else 200)


@cinema_admin_required
@require_http_methods(["GET", "POST"])
def cinema_movie_delete(request, pk):
    movie = get_object_or_404(CinemaMovie, pk=pk)
    if request.method == "POST":
        movie.delete()
        messages.success(request, "Kino o'chirildi.")
        return redirect(f"{reverse('cinema')}?tab=movies")
    return render(request, "bot/cinema_movie.html", {"movie": movie, "confirm_delete": True})
