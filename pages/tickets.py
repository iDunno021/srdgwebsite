"""Stamp seat details onto the YAC Improv Night ticket template and email them out."""
import base64
import io
from pathlib import Path

import resend
from django.conf import settings
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import white
from reportlab.pdfgen import canvas

TEMPLATE = Path(settings.BASE_DIR) / 'pages' / 'assets' / 'ticket_template.pdf'

# Centres of the two blank rules under the ROW / SEAT labels, in PDF points.
# The rules sit at y=29.7 with only 4.4pt of clearance to the labels above,
# so the values go in the open space below them.
ROW_CENTRE_X = 90.0
SEAT_CENTRE_X = 134.0
VALUE_BASELINE_Y = 18.0
VALUE_FONT = 'Times-Roman'
VALUE_SIZE = 11


def build_ticket_pdf(seat):
    """Return the template as PDF bytes with this seat's row and number filled in."""
    page = PdfReader(TEMPLATE).pages[0]
    width, height = float(page.mediabox.width), float(page.mediabox.height) 

    overlay = io.BytesIO()
    c = canvas.Canvas(overlay, pagesize=(width, height))
    c.setFillColor(white)
    c.setFont(VALUE_FONT, VALUE_SIZE)
    c.drawCentredString(ROW_CENTRE_X, VALUE_BASELINE_Y, seat.row)
    c.drawCentredString(SEAT_CENTRE_X, VALUE_BASELINE_Y, str(seat.number))
    c.save()
    overlay.seek(0)

    page.merge_page(PdfReader(overlay).pages[0])
    writer = PdfWriter()
    writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def send_ticket_email(to, event, seats, subject_prefix=''):
    """Email one buyer their stamped tickets, one PDF attachment per seat."""
    resend.api_key = settings.RESEND_API_KEY
    many = len(seats) > 1
    return resend.Emails.send({
        "from": "noreply@srdg.co.nz",
        "to": to,
        "subject": f"{subject_prefix}Your tickets for {event.title}",
        "html": f"""
            <h2>Thank you for purchasing a ticket.</h2>
            <p>Your seats: <strong>{", ".join(str(s) for s in seats)}</strong></p>
            <p>Your {"tickets are" if many else "ticket is"} attached to this email —
            print {"them" if many else "it"} or show on your phone at the door.
            If the attachment doesn't come through, don't worry, just show us this email/receipt at the door.</p>
            <p>Enjoy the show!</p>
        """,
        "attachments": [{
            "filename": f"YAC-Improv-Night-{seat}.pdf",
            "content": base64.b64encode(build_ticket_pdf(seat)).decode(),
        } for seat in seats],
    })
