from zope.interface import Interface
from zope import schema
from Products.CMFCore.utils import getToolByName
from mako.template import Template


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

    thankyou_with_confirmation_subject = schema.TextLine(
        title=u"Thank you with confirmation Subject")
    thankyou_with_confirmation_htmlbody = schema.Text(
        title=u"Thank you with confirmation HTML Body")
    thankyou_with_confirmation_textbody = schema.Text(
        title=u"Thank you with confirmation Plain Text Body")

    roster_subject = schema.Text(title=u"Roster Subject")
    roster_htmlbody = schema.Text(title=u"Roster HTML Body")
    roster_textbody = schema.Text(title=u"Roster Plain Text Body")


def sendEMail(emevent, emailtype, mto=[], reg=None, defattachments=[],
              deffrom=None, defsubject=None, defmsg=None):
    from email import encoders
    from email import MIMEText
    from email.mime.base import MIMEBase
    from email import MIMEMultipart

    mfrom = deffrom
    msubject = defsubject
    mbody = defmsg
    mattachments = defattachments

    mh = getToolByName(emevent, 'MailHost')

    if emailtype == 'thank you':
        mfrom = emevent.thankYouEMailFrom
        msubject = emevent.thankYouEMailSubject
        mbody = emevent.thankYouEMailBody

    elif emailtype == 'on waiting list':
        mfrom = emevent.waitingListEMailFrom
        msubject = emevent.waitingListEMailSubject
        mbody = emevent.waitingListEMailBody

    elif emailtype == 'registration full':
        mfrom = emevent.registrationFullEMailFrom
        msubject = emevent.registrationFullEMailSubject
        mbody = emevent.registrationFullEMailBody

    elif emailtype == 'confirmation':
        #mtemplate = 'email_confirmation.pt'
        pass
    elif emailtype == 'announcement':
        #mtemplate = 'email_announcement.pt'
        pass
    elif emailtype == 'other':
        #mtemplate = 'email_other.pt'
        pass

    if mfrom == None or mfrom == '':
        return False

    template = Template(mbody)
    message = template.render(emevent=emevent, reg=reg)

    for address in mto:
        msg = None
        if mattachments != None and len(mattachments) > 0:
            msg = MIMEMultipart(message)
            msg['Subject'] = msubject
            msg['From'] = mfrom

            for attachment in mattachments:
                amsg = MIMEBase('application', 'octet-stream')
                amsg.set_payload(attachment['data'])
                encoders.encode_base64(amsg)
                amsg.add_header('Content-Disposition', 'attachment',
                                filename=attachment['name'])
                msg.attach(amsg)
        else:
            msg = MIMEText(message)
            msg['Subject'] = msubject
            msg['From'] = mfrom

        msg['To'] = address
        mh.send(msg)

    #mh.send('message', 'to@example.com', 'from@example.com', 'subject')

    return True
