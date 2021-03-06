from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.app.component.hooks import getSite
from zope.component import getUtility
from zope.interface import Interface

from collective.eventmanager.registration import generateRegistrationHash
from collective.eventmanager.utils import Template


class IEMailTemplateSettings(Interface):
    announcement_subject = schema.Text(title=u"Announcement Subject")
    announcement_htmlbody = schema.Text(title=u"Announcement HTML Body")
    announcement_textbody = schema.Text(title=u"Announcement Plain Text Body")

    confirmation_subject = schema.TextLine(title=u"Confirmation Subject")
    confirmation_htmlbody = schema.Text(title=u"Confirmation HTML Body")
    confirmation_textbody = schema.Text(title=u"Confirmation Plain Text Body")

    onwaitinglist_subject = schema.TextLine(title=u"On waiting list Subject")
    onwaitinglist_htmlbody = schema.Text(title=u"On waiting list HTML Body")
    onwaitinglist_textbody = schema.Text(
        title=u"On waiting list Plain Text Body")

    other_subject = schema.TextLine(title=u"Other Subject")
    other_htmlbody = schema.Text(title=u"Other HTML Body")
    other_textbody = schema.Text(title=u"Other Plain Text Body")

    registrationfull_subject = schema.TextLine(
        title=u"Registraion full Subject")
    registrationfull_htmlbody = schema.Text(
        title=u"Registraion full HTML Body")
    registrationfull_textbody = schema.Text(
        title=u"Registraion full Plain Text Body")

    thankyou_subject = schema.TextLine(title=u"Thank you Subject")
    thankyou_htmlbody = schema.Text(title=u"Thank you HTML Body")
    thankyou_textbody = schema.Text(title=u"Thank you Plain Text Body")

    roster_subject = schema.Text(title=u"Roster Subject")
    roster_htmlbody = schema.Text(title=u"Roster HTML Body")
    roster_textbody = schema.Text(title=u"Roster Plain Text Body")


def sendEMail(emevent, emailtype, mto=[], reg=None, defattachments=[],
              deffrom=None, defsubject=None, defmsg=None):

    mtemplate = ''
    mfrom = deffrom
    msubject = defsubject
    mbody = defmsg
    additional_html_body = None
    additional_plain_body = None
    mattachments = defattachments

    mh = getToolByName(emevent, 'MailHost')
    registry = getUtility(IRegistry)

    # get data configured for this specific event
    if emailtype == 'thank you':
        mtemplate = 'thankyou'
        mfrom = emevent.thankYouEMailFrom
        msubject = emevent.thankYouEMailSubject
        mbody = emevent.thankYouEMailBody

    elif emailtype == 'on waiting list':
        mtemplate = 'onwaitinglist'
        mfrom = emevent.waitingListEMailFrom
        msubject = emevent.waitingListEMailSubject
        mbody = emevent.waitingListEMailBody

    elif emailtype == 'registration full':
        mtemplate = 'registrationfull'
        mfrom = emevent.registrationFullEMailFrom
        msubject = emevent.registrationFullEMailSubject
        mbody = emevent.registrationFullEMailBody

    elif emailtype == 'confirmation':
        mtemplate = 'confirmation'
        if emevent.thankYouIncludeConfirmation and reg is not None:
            # only include a confirmation link where a registration has
            #   been approved.
            confirmtext = ''
            confirmhtml = ''
            portal = getSite()
            wf = getToolByName(portal, 'portal_workflow')
            regstatus = wf.getStatusOf(
                'collective.eventmanager.Registration_workflow',
                reg)
            if regstatus is not None \
                    and regstatus['review_state'] == 'approved':
                confirmreghash = generateRegistrationHash('confirmation', reg)
                confirmtext = """
Please visit the following URL in order to confirm your registration:

%s/confirm-registration?h=%s


""" % (emevent.absolute_url(), confirmreghash)
                confirmhtml = '<br />Please ' \
                '<a href="%s/confirm-registration?h=%s">confirm your ' \
                'registration</a>.</div><br /><br />' \
                % (emevent.absolute_url(), confirmreghash)

            # put together the final messages
            cancelreghash = generateRegistrationHash('cancel', reg)
            additional_plain_body = """
=======================%s
If you'd like to cancel your registration, please visit the following URL:

%s/cancel-registration?h=%s""" % (confirmtext,
                                  emevent.absolute_url(), cancelreghash)
            additional_html_body = \
                '<div>=======================%s<div>' \
                'You may <a href="%s/cancel-registration?h=%s">cancel your ' \
                'registration</a> at any time.</div>' \
                % (confirmhtml,
                   emevent.absolute_url(), cancelreghash)

    elif emailtype == 'announcement':
        mtemplate = 'announcement'

    elif emailtype == 'other':
        mtemplate = 'other'

    if mfrom == None or mfrom == '':
        return False

    # get the keys for each of the registry entries that define the
    # email templates
    registrykey = "collective.eventmanager.emailtemplates" \
                  ".IEMailTemplateSettings.%s_%s"
    tsubkey = registrykey % (mtemplate, 'subject')
    thtmlkey = registrykey % (mtemplate, 'htmlbody')
    tplainkey = registrykey % (mtemplate, 'textbody')

    # get the site wide templates
    tsub = registry.records[tsubkey].value
    thtml = registry.records[thtmlkey].value
    tplain = registry.records[tplainkey].value

    subtemplate = Template(tsub)
    htmltemplate = Template(thtml)
    plaintemplate = Template(tplain)

    messagetemplate = Template(mbody)

    # apply results of event template render to site wide templates
    messageresult = messagetemplate.render(emevent=emevent).decode('utf-8')
    messagehtml = htmltemplate.render(
        emevent=emevent,
        event_content=messageresult)
    messageplain = plaintemplate.render(
        emevent=emevent,
        event_content=messageresult)

    if additional_html_body is not None:
        messagehtml += additional_html_body
    if additional_plain_body is not None:
        messageplain += additional_plain_body

    subject = subtemplate.render(emevent=emevent, event_content=msubject)

    # create a multipart message to hold both a text and html version
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject.decode('utf-8')
    msg['From'] = mfrom.encode('ascii')
    msgpart1 = MIMEText(messageplain, 'plain', 'utf-8')
    msgpart2 = MIMEText(messagehtml, 'html', 'utf-8')
    msg.attach(msgpart1)
    msg.attach(msgpart2)

    # if there were any attachments, then add them to the message
    if mattachments != None and len(mattachments) > 0:
        for attachment in mattachments:
            apart = MIMEBase('application', 'octet-stream')
            apart.set_payload(attachment['data'])
            encoders.encode_base64(apart)
            apart.add_header('Content-Disposition', 'attachment',
                            filename=attachment['name'])
            msg.attach(apart)

    # send a separate message to each address
    for address in mto:
        msg['To'] = address.encode('ascii')
        mh.send(msg.as_string(), address, mfrom, subject)
        #mh.send(msg)

    #mh.send('message', 'to@example.com', 'from@example.com', 'subject')

    return True
