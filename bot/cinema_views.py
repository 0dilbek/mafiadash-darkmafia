import logging

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError, connection, transaction
from django.db.models import BigIntegerField, Count, DateTimeField, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auth import admin_required
from .cinema_forms import CinemaPlanForm
from .cinema_models import (
    CinemaChannel, CinemaMovie, CinemaPlan, CinemaPurchase, CinemaSubscription, CinemaViewer,
)
from .models import Profile, User


logger = logging.getLogger(__name__)


def cinema_audience(*, tracking_available):
    # The shared User table also contains Mafia-only users. Include only people
    # with evidence of a Cinema interaction; offers count even without payment.
    known = Q(pk__in=CinemaPurchase.objects.values('user_id')) | Q(
        pk__in=CinemaSubscription.objects.values('user_id')
    )
    if tracking_available:
        known |= Q(pk__in=CinemaViewer.objects.values('user_id'))
    return User.objects.filter(is_bot=False).filter(known)


@admin_required
@require_http_methods(['GET', 'POST'])
def cinema_dashboard(request):
    tab = request.GET.get('tab', 'subscriptions')
    if tab not in {'settings', 'movies', 'channels', 'subscriptions', 'purchases'}:
        tab = 'subscriptions'
    access = request.GET.get('access', 'all')
    if access not in {'all', 'premium', 'standard'}:
        access = 'all'
    context = {'tab': tab, 'q': request.GET.get('q', '').strip()[:100], 'access': access}
    status = 200
    try:
        plan, _ = CinemaPlan.objects.get_or_create(pk=1)
        form = CinemaPlanForm(request.POST if request.method == 'POST' else None, instance=plan)
        if request.method == 'POST':
            if form.is_valid():
                with transaction.atomic():
                    locked_plan = CinemaPlan.objects.select_for_update().get(pk=1)
                    for field in form.Meta.fields:
                        setattr(locked_plan, field, form.cleaned_data[field])
                    locked_plan.save(update_fields=[*form.Meta.fields, 'updated_at'])
                messages.success(request, 'Obuna sozlamalari saqlandi.')
                return redirect(f"{reverse('cinema')}?tab=settings")
            tab = context['tab'] = 'settings'
            status = 400
            # ModelForm validation mutates its instance even when fields fail.
            # The current-plan preview must still show the saved values.
            plan.refresh_from_db()
        now = timezone.now()
        tracking_available = CinemaViewer._meta.db_table in connection.introspection.table_names()
        audience = cinema_audience(tracking_available=tracking_available)
        paid = CinemaPurchase.objects.filter(paid_at__isnull=False)
        context.update({
            'form': form, 'plan': plan, 'now': now,
            'tracking_available': tracking_available,
            'viewer_count': audience.count(),
            'movie_count': CinemaMovie.objects.count(),
            'channel_count': CinemaChannel.objects.count(),
            'active_count': CinemaSubscription.objects.filter(user__is_bot=False, expires_at__gt=now).count(),
            'purchase_count': paid.count(),
            'revenue': paid.aggregate(total=Sum('price_diamonds'))['total'] or 0,
        })
        q = context['q']
        rows = None
        if tab == 'movies':
            rows = CinemaMovie.objects.order_by('-created_at', 'id')
            if q:
                rows = rows.filter(Q(code__icontains=q) | Q(message_text__icontains=q))
        elif tab == 'channels':
            rows = CinemaChannel.objects.annotate(request_total=Count('join_requests')).order_by('id')
            if q:
                rows = rows.filter(title__icontains=q)
        elif tab == 'subscriptions':
            balances = Profile.objects.filter(user_id=OuterRef('pk')).order_by('pk').values('diamond')[:1]
            expiry = CinemaSubscription.objects.filter(user_id=OuterRef('pk')).values('expires_at')[:1]
            visits = (Subquery(CinemaViewer.objects.filter(user_id=OuterRef('pk')).values('last_seen_at')[:1])
                      if tracking_available else Value(None, output_field=DateTimeField()))
            offers = CinemaPurchase.objects.filter(user_id=OuterRef('pk')).order_by('-created_at').values('created_at')[:1]
            subscriptions = CinemaSubscription.objects.filter(user_id=OuterRef('pk')).values('created_at')[:1]
            rows = audience.annotate(
                balance=Coalesce(Subquery(balances), Value(0), output_field=BigIntegerField()),
                premium_expires_at=Subquery(expiry),
                last_seen_at=Coalesce(visits, Subquery(offers), Subquery(subscriptions)),
            ).order_by(F('last_seen_at').desc(nulls_last=True), 'pk')
            if access == 'premium':
                rows = rows.filter(premium_expires_at__gt=now)
            elif access == 'standard':
                rows = rows.filter(Q(premium_expires_at__isnull=True) | Q(premium_expires_at__lte=now))
            if q:
                rows = rows.filter(Q(full_name__icontains=q) | Q(user_id__icontains=q))
        elif tab == 'purchases':
            rows = paid.select_related('user').order_by('-paid_at', 'id')
            if q:
                rows = rows.filter(Q(user__full_name__icontains=q) | Q(user__user_id__icontains=q))
        if rows is not None:
            context['page_obj'] = Paginator(rows, 25).get_page(request.GET.get('page'))
            context['rows'] = list(context['page_obj'])
        context['tabs'] = [
            ('subscriptions', 'Obunachilar', 'people', context['viewer_count']),
            ('movies', 'Kinolar', 'film', context['movie_count']),
            ('channels', 'Kanallar', 'broadcast', context['channel_count']),
            ('purchases', 'Xaridlar', 'receipt', context['purchase_count']),
            ('settings', 'Sozlamalar', 'sliders', None),
        ]
    except DatabaseError:
        logger.exception('Cinema ma’lumotlarini olish yoki saqlashda xato')
        context['storage_error'] = True
        status = 503
    return render(request, 'bot/cinema.html', context, status=status)
