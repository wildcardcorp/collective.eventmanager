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
    certificate_subtitle = schema.TextLine(title=u"Subtitle")
    certificate_prenamedesc = schema.TextLine(
                                title=u"Pre-Name Description",
                                default=u"In honor of your outstanding "
                                        u"performance and dedication we "
                                        u"gladly present this award to")
    certificate_postnamedesc = schema.TextLine(
                                title=u"Post-Name Description",
                                default=u"for completion of the "
                                        u"requirements for")
    certificate_awardtitle = schema.TextLine(title=u"Award Title")
    certificate_date = schema.TextLine(
                                    title=u"Date",
                                    default=unicode(DateTime().strftime("%x")))
    certificate_sigdesc = schema.Text(title=u"Signature Description")
    certificate_border = schema.Choice(
                                    title=u"Border",
                                    values=[u'Blue', u'Green', u'Gold'],
                                    default=u'Gold'
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
