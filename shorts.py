from django.core.mail import send_mail
from django.template import loader, Context

def template_mail(title,template,context,addr_from,addr_to,fail_silently=False):
    template = loader.get_template(template)
    context = Context(context)
    send_mail(
        title,
        template.render(context),
        addr_from,
        addr_to,
        fail_silently=fail_silently)
 
