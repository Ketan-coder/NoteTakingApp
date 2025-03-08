from io import BytesIO #A stream implementation using an in-memory bytes buffer
                       # It inherits BufferIOBase
 
from django.http import HttpResponse
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

# xhtml2pdf is a PDF generator using HTML and CSS
# It supports HTML 5 and CSS 2.1 (and some of CSS 3)
# It is completely written in pure Python so it is platform independent
from xhtml2pdf import pisa  


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()

    # Use 'utf-8' encoding instead of 'ISO-8859-1'
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def send_email(to_email, subject, title, body, anchor_link=None, anchor_text="Click Here"):
    """
    Sends a customizable email with an optional anchor link.
    
    :param to_email: Single email (str) or multiple emails (list)
    :param subject: Email subject
    :param title: Title shown in the email
    :param body: Email body (main text content)
    :param anchor_link: (Optional) Link to include in the email
    :param anchor_text: (Optional) Text for the anchor link (default: 'Click Here')
    """
    
    # Convert single email to list
    if isinstance(to_email, str):
        to_email = [to_email]
    
    # Construct anchor link if provided
    anchor_html = f'<p><a href="{anchor_link}" style="padding: 10px; background-color: #0076d1; color: white; text-decoration: none;">{anchor_text}</a></p>' if anchor_link else ""

    # Email content (HTML)
    html_content = f'''
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
    </head>
    <body style="font-family: 'Poppins', Arial, sans-serif; background: #ffffff; padding: 20px;">
        <h2 style="color: #0076d1;">{title}</h2>
        <p>{body}</p>
        {anchor_html}
        <p>If you did not request this, please ignore this email.</p>
    </body>
    </html>
    '''

    # Plain text fallback
    text_content = f"{title}\n\n{body}\n\n{anchor_link if anchor_link else ''}"

    # Send email
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()