"""Email tickets to people who already paid — e.g. buyers from before tickets were attached."""
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError

from pages.models import Event, Ticket
from pages.tickets import send_ticket_email


class Command(BaseCommand):
    help = 'Email stamped ticket PDFs to everyone holding a paid ticket for an event.'

    def add_arguments(self, parser):
        parser.add_argument('--event', type=int, required=True, help='Event id')
        parser.add_argument('--send', action='store_true', help='Actually send (otherwise dry run)')
        parser.add_argument('--email', help='Limit to this buyer')

    def handle(self, *args, **options):
        try:
            event = Event.objects.get(id=options['event'])
        except Event.DoesNotExist:
            raise CommandError(f"No event with id {options['event']}")

        tickets = Ticket.objects.filter(seat__event=event, status=Ticket.PAID).select_related('seat')
        if options['email']:
            tickets = tickets.filter(email__iexact=options['email'])

        buyers = defaultdict(list)
        for ticket in tickets:
            buyers[ticket.email].append(ticket.seat)
        if not buyers:
            self.stdout.write(self.style.WARNING('No paid tickets match.'))
            return

        for email, seats in buyers.items():
            seats.sort(key=lambda s: (s.row, s.number))
            label = ', '.join(str(s) for s in seats)
            if not options['send']:
                self.stdout.write(f'[dry run] would email {email} — {label}')
                continue
            try:
                send_ticket_email(email, event, seats)
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'FAILED {email}: {exc}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'sent {email} — {label}'))

        if not options['send']:
            self.stdout.write(self.style.WARNING(f'\nDry run — {len(buyers)} email(s) not sent. Re-run with --send.'))
