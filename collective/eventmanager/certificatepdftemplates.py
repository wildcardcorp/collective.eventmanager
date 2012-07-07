from DateTime import DateTime
from mako.template import Template
from plone.registry.interfaces import IRegistry
import StringIO
import xhtml2pdf.pisa as pisa
from zope import schema
from zope.component import getUtility
from zope.interface import Interface


class ICertificatePDFTemplateSettings(Interface):
    certificate_title = schema.TextLine(
                            title=u"Title",
                            default=u"Certificate of Completion")
    certificate_subtitle = schema.TextLine(title=u"Subtitle", required=False)
    certificate_prenamedesc = schema.TextLine(
                                title=u"Pre-Name Description",
                                default=u"In honor of your outstanding "
                                        u"performance and dedication we "
                                        u"gladly present this award to",
                                required=False)
    certificate_postnamedesc = schema.TextLine(
                                title=u"Post-Name Description",
                                default=u"for completion of the "
                                        u"requirements for",
                                required=False)
    certificate_awardtitle = schema.TextLine(title=u"Award Title",
                                             required=False)
    certificate_date = schema.TextLine(
                                    title=u"Date",
                                    default=unicode(DateTime().strftime("%x")),
                                    required=False)
    certificate_sigdesc = schema.Text(title=u"Signature Description",
                                      required=False)
    certificate_border = schema.Choice(
                                    title=u"Border",
                                    values=[u'Blue', u'Green', u'Gold'],
                                    default=u'Gold',
                                    required=False
                                )

    certificate_pdf_template = schema.Text(title=u"Certificate PDF Template")


def generateCertificate(registrations, portal_url, underlines_for_empty_values,
                        certtitle, certsubtitle, certprenamedesc,
                        certpostnamedesc, certawardtitle, certdate,
                        certsigdesc, certborder):

    registry = getUtility(IRegistry)
    certificatepdftemplatetext = registry.records[
            'collective.eventmanager.certificatepdftemplates'
            '.ICertificatePDFTemplateSettings.certificate_pdf_template'
        ].value
    certificatepdftemplate = Template(certificatepdftemplatetext)
    renderedcertificatepdfs = certificatepdftemplate.render(
            registrations=registrations,
            portal_url=portal_url,
            underlines_for_empty_values=underlines_for_empty_values,
            certtitle=certtitle,
            certsubtitle=certsubtitle,
            certprenamedesc=certprenamedesc,
            certpostnamedesc=certpostnamedesc,
            certawardtitle=certawardtitle,
            certdate=certdate,
            certsigdesc=certsigdesc,
            certborder=certborder
        )

    pdf = StringIO.StringIO()

    html = StringIO.StringIO(renderedcertificatepdfs)
    pisa.pisaDocument(html, pdf, raise_exception=True)
    assert pdf.len != 0, 'PDF generation utility returned empty PDF!'
    html.close()

    pdfcontent = pdf.getvalue()
    pdf.close()

    now = DateTime()
    filename = '%s-%s.pdf' % ('certificates', now.strftime('%Y%m%d'))

    return {'filename': filename, 'file': pdfcontent}


def getDefaultValueForCertField(field):
    registry = getUtility(IRegistry)
    value = registry.records[
        'collective.eventmanager.certificatepdftemplates'
        '.ICertificatePDFTemplateSettings.certificate_%s'
        % (field,)
    ].value

    # if the value is none now, that means the registry hasn't been saved
    # yet, so we need to get the default value, if any, from the
    # interface
    if value == None:
        value = ICertificatePDFTemplateSettings.get(
                    'certificate_%s' % (field,)).default

    # if the value is still none, then there is no default value set
    if value == None:
        return ''

    return value
