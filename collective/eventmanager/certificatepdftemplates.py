from zope.interface import Interface
from zope import schema


class ICertificatePDFTemplateSettings(Interface):
    certificate_pdf_template = schema.Text(title=u"Certificate PDF Template")
