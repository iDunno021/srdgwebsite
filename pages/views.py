import json
from collections import defaultdict
from datetime import timedelta
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import BooleanField, Case, Count, Q, Value, When
from django.utils import timezone
from .models import Member, Initiative, Event, Seminar, MemberRole, BlogPost, BlogImage, BlogAttachment, BlogReaction, ArtPiece, AboutPhoto, Seat, Ticket
from .forms import MemberForm, BlogPostForm, EventRSVPForm
from .utils import get_client_ip
from django.views import generic
import resend
import stripe
from django.conf import settings

ALLOWED_IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_ATTACHMENT_EXTS = {'pdf', 'doc', 'docx', 'txt'}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

def _validate_upload(f, allowed_exts):
    ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
    if ext not in allowed_exts:
        return f'"{f.name}" has an unsupported file type.'
    if f.size > MAX_UPLOAD_SIZE:
        return f'"{f.name}" is too large (max 10MB).'
    return None

SCHOOLS_BY_REGION = {
    'auckland': ['AGS', 'STC', 'STK', 'BAR', 'EGGS', 'KC', 'GDC', 'selwyn', 'DIO', 'RGT', 'DIL', 'ACGP', 'ACGS', 'WBC', 'WGC', 'MAC', 'SDCC', 'GBHS', 'other'],
    'bayofplenty': ['other'],
    'canterbury': ['other'],
    'gisbourne': ['other'],
    'hawkesbay': ['SJC', 'other'],
    'manawatuwhanganui': ['other'],
    'marlborough': ['other'],
    'nelson': ['other'],
    'northland': ['other'],
    'otago': ['other'],
    'southland': ['other'],
    'taranaki': ['other'],
    'tasman': ['other'],
    'waikato': ['other'],
    'wellington': ['other'],
    'westcoast': ['other'],
}

def home(request):
    total_members = Member.objects.count()
    total_initiatives = Initiative.objects.filter(hidden=False).count()
    schools_count = len([s for s in Member.SCHOOLS if s[0] != 'other'])
    total_activites = Seminar.objects.filter(hidden=False).count() + Event.objects.count()
    initiatives = Initiative.objects.filter(hidden=False)
    about_side_photos = list(AboutPhoto.objects.filter(slot='side'))
    about_middle_photos = list(AboutPhoto.objects.filter(slot='middle'))
    about_middle_photo = about_middle_photos[0] if about_middle_photos else None
    about_side_urls = [p.image.url for p in about_side_photos]
    about_middle_urls = [p.image.url for p in about_middle_photos]
    return render(request, 'pages/new_home.html', {
        'total_members': total_members,
        'total_initiatives': total_initiatives,
        'schools_count': schools_count,
        'total_activities': total_activites,
        'initiatives': initiatives,
        'about_side_photos': about_side_photos[:4],
        'about_middle_photo': about_middle_photo,
        'about_side_urls': about_side_urls,
        'about_middle_urls': about_middle_urls,
    })

def signup(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            if member.school == 'other':
                other_school = request.POST.get('other_school')
                if not other_school:
                    form.add_error(None, 'Please enter your school name.')
                    return render(request, 'pages/signup.html', {'form': form, 'schools_by_region': json.dumps(SCHOOLS_BY_REGION)})
                member.school = other_school
            member.save()
            return redirect('signup_success')
    else:
        form = MemberForm()
    return render(request, 'pages/signup.html', {'form': form, 'schools_by_region': json.dumps(SCHOOLS_BY_REGION)})

def signup_success(request):
    return render(request, 'pages/signup_success.html')

def staff(request):
    roles = sorted(MemberRole.objects.select_related('member').all(), key=lambda r: (r.member.first_name.lower() != 'amber' or r.member.last_name.lower() != 'cai'))
    committees = {
        'General Committee': [r for r in roles if r.committee == 'general'],
        'EduUnlocked': [r for r in roles if r.committee == 'ea'],
        'Politics of Tomorrow': [r for r in roles if r.committee == 'ype'],
        'Young Artists Collective': [r for r in roles if r.committee == 'yac'],
        'Administrative Committee': [r for r in roles if r.committee == 'administrative'],
        'Technical Committee': [r for r in roles if r.committee == 'technical'],
        'Outreach Department': [r for r in roles if r.committee == 'outreach'],
        'Finance Department': [r for r in roles if r.committee == 'finance'],
    }
    return render(request, 'pages/staff.html', {'committees': committees})

def contact(request):
    return render(request, 'pages/contact.html')

def _order_events(queryset):
    """Upcoming events first (soonest first), completed ones last."""
    return queryset.annotate(
        is_completed=Case(
            When(end_time__lt=timezone.now(), then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    ).order_by('is_completed', 'start_time')

def events(request):
    all_events = _order_events(Event.objects.select_related('initiative'))
    return render(request, 'pages/events.html', {'events': all_events})

def event_attend(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'pages/event_attend.html', {
        'event': event,
        'form': EventRSVPForm(),
    })

def calendar(request):
    status_colors = {'upcoming': '#C8391A', 'active': '#2e7d32', 'completed': '#1a4a7a'}

    events = [
        {
            'title': e.title,
            'start': e.start_time.isoformat(),
            'end': e.end_time.isoformat(),
            'color': status_colors[e.get_status],
            'url': f'/events/{e.id}/attend/',
        }
        for e in Event.objects.filter(start_time__isnull=False, end_time__isnull=False)
    ]
    seminars = [
        {
            'title': s.title,
            'start': s.start_time.isoformat(),
            'end': s.end_time.isoformat(),
            'url': f'/seminars/{s.slug}/',
            'color': status_colors[s.get_status],
        }
        for s in Seminar.objects.filter(hidden=False)
    ]
    return render(request, 'pages/calendar.html', {'calendar_events': events + seminars})

class SeminarView(generic.ListView):
    model = Seminar
    template_name = 'pages/seminars.html'
    context_object_name = 'seminars'
    queryset = Seminar.objects.filter(hidden=False)

def seminar_detail(request, slug):
    seminar = get_object_or_404(Seminar, slug=slug, hidden=False)
    custom = f'pages/seminars/{slug}.html'
    default = 'pages/seminars/seminar_base.html'
    try:
        get_template(custom)
        template = custom
    except:
        template = default
    return render(request, template, {'seminar': seminar})

class InitiativeView(generic.ListView):
    model = Initiative
    template_name = 'pages/initiatives.html'
    context_object_name = 'initiatives'
    queryset = Initiative.objects.filter(hidden=False).order_by('order', 'pk')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['art_pieces'] = ArtPiece.objects.filter(hidden=False)
        return ctx

def initiative_detail(request, slug):
    initiative = get_object_or_404(Initiative, slug=slug, hidden=False)
    custom = f'pages/initiatives/{slug}.html'
    default = 'pages/initiatives/initiative_base.html'  
    try:
        get_template(custom)
        template = custom
    except:
        template = default
    return render(request, template, {
        'initiative': initiative,
        'events': _order_events(initiative.events.all()),
    })

class BlogView(generic.ListView):
    model = BlogPost
    template_name = 'pages/blog.html'
    context_object_name = 'posts'

    def get_queryset(self):
        qs = BlogPost.objects.filter(approved=True).annotate(
            like_count=Count('reactions', filter=Q(reactions__reaction=BlogReaction.LIKE)),
        )
        if self.request.GET.get('sort') == 'liked':
            return qs.order_by('-like_count', '-published_at')
        return qs.order_by('-published_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_sort'] = self.request.GET.get('sort', 'recent')
        return ctx

def blog_detail(request, id):
    post = get_object_or_404(BlogPost, id=id, approved=True)
    like_count = post.reactions.filter(reaction=BlogReaction.LIKE).count()
    dislike_count = post.reactions.filter(reaction=BlogReaction.DISLIKE).count()
    user_reaction = None
    ip = get_client_ip(request)
    if ip != 'unknown':
        existing = post.reactions.filter(ip_address=ip).first()
        user_reaction = existing.reaction if existing else None
    return render(request, 'pages/blog_detail.html', {
        'post': post,
        'like_count': like_count,
        'dislike_count': dislike_count,
        'user_reaction': user_reaction,
    })

def blog_react(request, id, reaction):
    post = get_object_or_404(BlogPost, id=id, approved=True)
    if request.method == 'POST' and reaction in (BlogReaction.LIKE, BlogReaction.DISLIKE):
        ip = get_client_ip(request)
        if ip != 'unknown':
            existing = BlogReaction.objects.filter(post=post, ip_address=ip).first()
            if existing and existing.reaction == reaction:
                existing.delete()
            elif existing:
                existing.reaction = reaction
                existing.save(update_fields=['reaction'])
            else:
                BlogReaction.objects.create(post=post, ip_address=ip, reaction=reaction)
    return redirect('blog_detail', id=id)

def create_blog(request):
    if request.method == 'POST':
        ip = get_client_ip(request)
        cache_key = f'blog_create_{ip}'
        if cache.get(cache_key):
            return render(request, 'pages/create_blog.html', {
                'form': BlogPostForm(),
                'rate_limited': True,
            })
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            errors = []
            for f in request.FILES.getlist('images'):
                if err := _validate_upload(f, ALLOWED_IMAGE_EXTS):
                    errors.append(err)
            for f in request.FILES.getlist('attachments'):
                if err := _validate_upload(f, ALLOWED_ATTACHMENT_EXTS):
                    errors.append(err)

            if errors:
                return render(request, 'pages/create_blog.html', {'form': form, 'upload_errors': errors})

            post = form.save()
            for image in request.FILES.getlist('images'):
                BlogImage.objects.create(post=post, image=image)
            for attachment in request.FILES.getlist('attachments'):
                BlogAttachment.objects.create(post=post, file=attachment, name=attachment.name)
            cache.set(cache_key, True, 3600)
            return redirect('blog')
    else:
        form = BlogPostForm()
    return render(request, 'pages/create_blog.html', {'form': form})

def event_rsvp(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventRSVPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            member = Member.objects.filter(email=email).first()
            rsvp = form.save(commit=False)
            rsvp.event = event
            if member:
                rsvp.member = member
            try:
                rsvp.save()
            except IntegrityError:
                messages.error(request, "You've already registered for this event with that email")
                return redirect('event_attend', event_id=event_id)
            try:
                resend.api_key = settings.RESEND_API_KEY
                resend.Emails.send({
                    "from": "noreply@srdg.co.nz",
                    "to": email,
                    "subject": f"You've registered for {event.title}!",
                    "html": f"""
                        <h2> You're in! </h2>
                        <p>Thanks for registering for the <strong>{event.title}</strong>.</p>
                        <p>We'll see you there!</p>
                    """
                })
            except Exception as e:
                print(f"Email failed: {e}")
            messages.success(request, "You're registered! We'll see you there.")
            return redirect('event_attend', event_id=event_id)
    return redirect('events')

def partners(request):
    total_members = Member.objects.count()
    schools_count = len([s for s in Member.SCHOOLS if s[0] != 'other'])

    return render(request, 'pages/partners.html', {
        'total_members': total_members,
        'schools_count': schools_count,
    })


DONATION_AMOUNTS_NZD = [5, 10, 25, 50, 100]


def network263(request):
    return render(request, 'pages/network263.html', {'donated': request.GET.get('donated')})

def debate(request):
    return render(request, 'pages/debate.html')


def donate_checkout(request):
    if request.method != 'POST':
        return redirect('network263')

    try:
        amount = int(request.POST.get('amount', 0))
    except ValueError:
        amount = 0
    if amount not in DONATION_AMOUNTS_NZD:
        return redirect('network263')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        submit_type='donate',
        line_items=[{
            'price_data': {
                'currency': 'nzd',
                'product_data': {'name': 'Donation to SRDG — Network 263'},
                'unit_amount': amount * 100,
            },
            'quantity': 1,
        }],
        payment_intent_data={'description': '(From SRDG website)'},
        success_url=request.build_absolute_uri('/network263/donate/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri('/network263/') + '?donated=cancel',
    )
    return redirect(session.url)


def donate_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('network263')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        return redirect('network263')

    if session.payment_status != 'paid':
        return redirect('network263')

    return render(request, 'pages/donate_success.html', {
        'amount': session.amount_total / 100,
    })


TICKET_PRICE_NZD = 15
PREMIUM_ROWS = ('A', 'B')
PREMIUM_PRICE_NZD = 17
HOLD_MINUTES = 30
TICKETS_ON_SALE = True  # flip to True when ticket sales open


def seat_price(seat):
    return PREMIUM_PRICE_NZD if seat.row in PREMIUM_ROWS else TICKET_PRICE_NZD


def event_tickets(request, event_id):
    event = get_object_or_404(Event, id=event_id, ticketed=True)
    now = timezone.now()
    seats = list(event.seats.select_related('ticket').all())
    for seat in seats:
        ticket = getattr(seat, 'ticket', None)
        # ponytail: is_accessible doubles as "held back from sale" — no separate flag/migration
        seat.taken = seat.is_accessible or bool(ticket and (ticket.status == Ticket.PAID or (ticket.hold_expires_at and ticket.hold_expires_at > now)))
        seat.price = seat_price(seat)
    return render(request, 'pages/event_tickets.html', {
        'event': event,
        'seats': seats,
        'ticket_price': TICKET_PRICE_NZD,
        'premium_price': PREMIUM_PRICE_NZD,
        'tickets_on_sale': TICKETS_ON_SALE,
    })


def event_tickets_checkout(request, event_id):
    event = get_object_or_404(Event, id=event_id, ticketed=True)
    if not TICKETS_ON_SALE:
        return redirect('event_tickets', event_id=event_id)
    if request.method != 'POST':
        return redirect('event_tickets', event_id=event_id)

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    seat_ids = request.POST.getlist('seat_ids')
    if not name or not email or not seat_ids:
        messages.error(request, 'Please enter your details and select at least one seat.')
        return redirect('event_tickets', event_id=event_id)

    now = timezone.now()
    with transaction.atomic():
        seats = list(Seat.objects.select_for_update().filter(event=event, id__in=seat_ids))
        if len(seats) != len(seat_ids):
            messages.error(request, 'One of the selected seats no longer exists.')
            return redirect('event_tickets', event_id=event_id)

        if any(seat.is_accessible for seat in seats):
            messages.error(request, 'One of the selected seats is not available for purchase.')
            return redirect('event_tickets', event_id=event_id)

        for seat in seats:
            existing = Ticket.objects.filter(seat=seat).first()
            if existing and (existing.status == Ticket.PAID or (existing.hold_expires_at and existing.hold_expires_at > now)):
                messages.error(request, 'Sorry, one of your selected seats was just taken. Please choose again.')
                return redirect('event_tickets', event_id=event_id)
            if existing:
                existing.delete()

        Ticket.objects.bulk_create([
            Ticket(seat=seat, name=name, email=email, hold_expires_at=now + timedelta(minutes=HOLD_MINUTES))
            for seat in seats
        ])

    seats_by_price = defaultdict(list)
    for seat in seats:
        seats_by_price[seat_price(seat)].append(seat)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'nzd',
                'product_data': {'name': f'{event.title} — {", ".join(sorted(str(s) for s in group))}'},
                'unit_amount': price * 100,
            },
            'quantity': len(group),
        } for price, group in sorted(seats_by_price.items())],
        payment_intent_data={'receipt_email': email},
        expires_at=int((now + timedelta(minutes=HOLD_MINUTES)).timestamp()),
        success_url=request.build_absolute_uri(f'/events/{event.id}/tickets/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(f'/events/{event.id}/tickets/cancel/') + '?session_id={CHECKOUT_SESSION_ID}',
    )
    Ticket.objects.filter(seat__in=seats).update(stripe_session_id=session.id)
    return redirect(session.url)


def event_tickets_success(request, event_id):
    session_id = request.GET.get('session_id')
    event = get_object_or_404(Event, id=event_id)
    if not session_id:
        return redirect('event_tickets', event_id=event_id)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        return redirect('event_tickets', event_id=event_id)

    if session.payment_status != 'paid':
        return redirect('event_tickets', event_id=event_id)

    pending = list(Ticket.objects.filter(stripe_session_id=session_id, status=Ticket.PENDING).select_related('seat'))
    Ticket.objects.filter(id__in=[t.id for t in pending]).update(status=Ticket.PAID, hold_expires_at=None)
    tickets = pending or list(Ticket.objects.filter(stripe_session_id=session_id, status=Ticket.PAID).select_related('seat'))
    return render(request, 'pages/event_tickets_success.html', {
        'event': event,
        'seats': [t.seat for t in tickets],
    })


def event_tickets_cancel(request, event_id):
    session_id = request.GET.get('session_id')
    if session_id:
        Ticket.objects.filter(stripe_session_id=session_id, status=Ticket.PENDING).delete()
    messages.info(request, 'Checkout cancelled — your seats have been released.')
    return redirect('event_tickets', event_id=event_id)
