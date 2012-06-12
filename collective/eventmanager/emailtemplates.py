from zope.interface import Interface
from zope import schema
from zope.component import getUtility
from mako.template import Template
from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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

    elif emailtype == 'announcement':
        mtemplate = 'announcement'

    elif emailtype == 'other':
        mtemplate = 'other'

    if mfrom == None or mfrom == '':
        return False

    # get the site wide templates
    tsub = registry.records['collective.eventmanager.emailtemplates'
                            '.IEMailTemplateSettings.' + mtemplate + '_subject'
                            ].value
    thtml = registry.records['collective.eventmanager.emailtemplates'
                            '.IEMailTemplateSettings.' + mtemplate + '_htmlbody'
                            ].value
    tplain = registry.records['collective.eventmanager.emailtemplates'
                            '.IEMailTemplateSettings.' + mtemplate + '_textbody'
                            ].value

    subtemplate = Template(tsub)
    htmltemplate = Template(thtml)
    plaintemplate = Template(tplain)

    messagetemplate = Template(mbody)

    # apply results of event template render to site wide templates
    messageresult = messagetemplate.render(emevent=emevent)
    messagehtml = htmltemplate.render(emevent=emevent, event_content=messageresult)
    messageplain = plaintemplate.render(emevent=emevent, event_content=messageresult)

    subject = subtemplate.render(emevent=emevent, event_content=msubject)

    # create a multipart message to hold both a text and html version
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = mfrom
    msgpart1 = MIMEText(messageplain, 'plain')
    msgpart2 = MIMEText(messagehtml, 'html')
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
        msg['To'] = address
        mh.send(msg.as_string(), address, mfrom, subject)
        #mh.send(msg)

    #mh.send('message', 'to@example.com', 'from@example.com', 'subject')

    return True

