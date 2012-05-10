from five import grok
from zope import schema, interface
from plone.directives import form
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from plone.namedfile.field import NamedBlobFile
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarMarker
from datetime import datetime
from Products.CMFCore.utils import getToolByName
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from Products.Five.browser import BrowserView

from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

from collective.eventmanager.config import BASE_TYPE_NAME
from collective.eventmanager.interfaces import ILayer
from collective.eventmanager import EventManagerMessageFactory as _
from collective.z3cform.mapwidget.widget import MapFieldWidget


registrationRowAvailableFieldTypes = SimpleVocabulary(
    [SimpleTerm(value=u'TextLine', title=u'Text Line'),
     SimpleTerm(value=u'Text', title=u'Text Area'),
     SimpleTerm(value=u'Float', title=u'Number'),
     SimpleTerm(value=u'Bool', title=u'Check Box'),
     SimpleTerm(value=u'Datetime', title=u'Date/Time'),
     SimpleTerm(value=u'URI', title=u'URL')]
    )


class IRegistrationFieldRow(interface.Interface):
    name = schema.TextLine(
            title=u"Name",
            required=True,
        )

    fieldtype = schema.Choice(
            title=u"Field Type",
            vocabulary=registrationRowAvailableFieldTypes,
            required=True,
        )
    required = schema.Bool(
            title=u"Required?",
            required=True,
            default=True,
        )


class IEMEvent(form.Schema, ISolgemaFullcalendarMarker):
    """An event"""

    title = schema.TextLine(
            title=_(u"Event Name"),
        )

    description = schema.Text(
            title=_(u"Description/Notes"),
        )

    start = schema.Datetime(
            title=_(u"Start Date/Time"),
            description=_(u"Date and time the Event starts"),
            required=True,
            default=datetime.today()
        )

    end = schema.Datetime(
            title=_(u"End Date/Time"),
            description=_(u"Date and time the Event ends"),
            required=True,
            default=datetime.today()
        )

    enableSessions = schema.Bool(
            title=_(u"Enable Sessions"),
            description=_(u"If checked, the em event display will be updated "
                          u"with a session calendar showing all sessions "
                          u"registered for the event. <em>NOTE</em> if this "
                          u"option is disabled after the event has been "
                          u"created, the session folders will be deleted, "
                          u"along with all sessions added to it."),
            required=True,
            default=True,
        )

    registrationOpen = schema.Datetime(
            title=_(u"Registration Open"),
            description=_(u"Date and time registration for the event is open"),
            required=True,
            default=datetime.today()
        )

    registrationClosed = schema.Datetime(
            title=_(u"Registration Closed"),
            description=_(u"Date and time registration for the event "
                          u"is closed"),
            required=False,
        )

    form.widget(location=MapFieldWidget)
    location = schema.TextLine(
            title=_(u"Location"),
            description=_(u"Address of the location of the event"),
            required=False,
        )

    locationDescription = schema.Text(
            title=_(u"Description of Location"),
            description=_(u"A short description of the location"),
            required=False,
        )

    maxRegistrations = schema.Int(
            title=_(u"Maximum Registrations Available"),
            description=_(u"The maximum amount of registrations to accept "
                          u"before closing registration, or, if enabled, "
                          u"putting registrants on a waiting list -- "
                          u"leave empty for no limit"),
            required=False,
        )

    enableWaitingList = schema.Bool(
            title=_(u"Enable Waiting List"),
            description=_(u"When enabled, if registration is private or "
                          u"the event is private, then registrations get "
                          u"approved until the max registration amount is "
                          u"reached (if there is a maximum), and then "
                          u"registrations get placed on the waiting list. "
                          u"If registration is public, and this option is "
                          u"enabled then if maximum registrations have been "
                          u"met, registrations are put on to the waiting "
                          u"list. Otherwise, registrations are approved."),
            required=True,
            default=False,
        )

    flyer = NamedBlobFile(
            title=_(u"Flyer"),
            description=_(u"A flyer for the event"),
            required=False,
        )

    requirePayment = schema.Bool(
            title=_(u"Require Payment with Registration"),
            description=_(u"If payment should be required at the time of "
                          u"registration, check this field"),
            required=True,
            default=False
        )

    privateRegistration = schema.Bool(
            title=_(u"Private Registration"),
            description=_(u"Require that all registration be done manually by "
                          u"a site administrator"),
            required=True,
            default=False,
        )

    privateEvent = schema.Bool(
            title=_(u"Private Event"),
            description=_(u"Hide the event from the public calendar, potential"
                          u" registrants must be either added manually or "
                          u"receive an announcement email containing a "
                          u"registration link"),
            required=True,
            default=False,
        )

    # === REGISTRATION FIELDS ===
    form.fieldset(
            "registrationfields",
            label=_(u"Registration Fields"),
            fields=[
                'registrationFields'
            ]
        )

    form.widget(registrationFields=DataGridFieldFactory)
    registrationFields = schema.List(
            title=_(u"Registration Fields"),
            description=_(u"All registrations have a name and email field. "
                          u"Configure any additional fields you wish to "
                          u"associated with a registration for this event "
                          u"here."),
            value_type=DictRow(
                    title=_(u"Registration Field"),
                    schema=IRegistrationFieldRow
                ),
            required=False,
        )

    # === CONTACT/PRESENTER ===
    form.fieldset(
            "contactsettings",
            label=_(u"Contact Settings"),
            fields=[
                'contactName',
                'contactDetails'
            ]
        )
    contactName = schema.TextLine(
            title=_(u"Contact/Presenter Name"),
            description=_(u"A name for the primary contact or presenter of "
                          u"this event"),
            required=False,
        )

    contactDetails = schema.Text(
            title=_(u"Contact/Presenter Details"),
            description=_(u"Put information about the contact/presentor, "
                          u"including phone, email, twitter handle, and "
                          u"any other descriptive information about the "
                          u"person"),
            required=False,
        )

    # === ANNOUNCEMENT EMAIL ===
    #form.fieldset(
    #        "announcmentemailsettings",
    #        label=_(u"Announcement EMail Settings"),
    #        fields=[
    #            'sendAnnouncementEMail',
    #            'sendAnnouncementEMailTo',
    #            'announcementEMailFrom',
    #            'announcementEMailSubject',
    #            'announcementEMailBody'
    #        ])

    ## sent to a list of email addresses, either manually by an administrator
    ## or automatically when registration opens
    #sendAnnouncementEMail = schema.Bool(
    #        title=_(u"Send Announcement EMail Automatically"),
    #        description=_(u"Send an announcement email when event registration"
    #                      u" opens, otherwise an administrator can send"
    #                      u" the annoucement email at any time"),
    #        required=True,
    #        default=False,
    #    )
    #announcementEMailFrom = schema.TextLine(
    #        title=_(u"EMail address to send Announcement EMail from"),
    #        description=_(u"The EMail address to use in the From field"),
    #        required=False,
    #    )
    #sendAnnouncementEMailTo = schema.Text(
    #        title=_(u"EMail addresses to send Announcement to"),
    #        description=_(u"list of addresses separated by commas or newlines "
    #                      u"to send the announcement email to. This field "
    #                      u"can be left blank if the announcement will "
    #                      u"not be sent automatically"),
    #        required=False,
    #    )
    #announcementEMailSubject = schema.TextLine(
    #        title=_(u"Annoucement EMail Subject"),
    #        description=_(u"The subject of the EMail announcing the event"),
    #        required=False,
    #        default=_(u"A New Event is Available"),
    #    )
    #announcementEMailBody = schema.Text(
    #        title=_(u"Announcement EMail Body"),
    #        description=_(u"The content of the EMail announcing the event"),
    #        required=False,
    #        default=_(u"")
    #    )

    # === THANK YOU EMAIL ===
    form.fieldset(
            "thankyouemailsettings",
            label=_(u"Thank You EMail Settings"),
            fields=[
                'thankYouIncludeConfirmation',
                'thankYouEMailFrom',
                'thankYouEMailSubject',
                'thankYouEMailBody',
                'thankYouEMailAttachment1',
                'thankYouEMailAttachment2',
                'thankYouEMailAttachment3',
                'thankYouEMailAttachment4'
            ])

    # this email gets sent as soon as a person has completed registration
    # if the confirmation is to be included, then a confirmation message and
    # link will be included in the sent email. A separate confirmation email
    # can be sent from the EMail Sender tab of an EM Event page.
    thankYouIncludeConfirmation = schema.Bool(
            title=_(u"Include Confirmation Link and Message"),
            description=_(u"When enabled, a confirmation message and link "
                          u"will be included in the the thank you "
                          u"message -- you can also manually send "
                          u"confirmation messages via the 'EMail Sender' tab"),
            required=True,
            default=False,
        )
    thankYouEMailFrom = schema.TextLine(
            title=_(u"EMail address to send Thank You from"),
            description=_(u"The EMail address to use in the From field"),
            required=False,
        )
    thankYouEMailSubject = schema.TextLine(
            title=_(u"Thank You EMail Subject"),
            description=_(u"The subject of the EMail a person receives after "
                          u"registering for the event"),
            required=True,
            default=_(u"Registration Complete"),
        )
    thankYouEMailBody = schema.Text(
            title=_(u"Thank You EMail Body"),
            description=_(u"The content of the EMail a person receives after "
                          u"registering for the event, NOTE: this message "
                          u"appears before any registration details, such "
                          u"as a registration number or cancellation "
                          u"link"),
            required=True,
            default=_(u"Thank you for registering for this event."),
        )

    # these are the values that are automatically included when a
    # thankyou/confirmation email is sent
    thankYouEMailAttachment1 = NamedBlobFile(
            title=_(u"First email attachment"),
            description=_(u"A file attached to the email"),
            required=False,
        )

    thankYouEMailAttachment2 = NamedBlobFile(
            title=_(u"Second email attachment"),
            description=_(u"A file attached to the email"),
            required=False,
        )

    thankYouEMailAttachment3 = NamedBlobFile(
            title=_(u"Third email attachment"),
            description=_(u"A file attached to the email"),
            required=False,
        )

    thankYouEMailAttachment4 = NamedBlobFile(
            title=_(u"Fourth email attachment"),
            description=_(u"A file attached to the email"),
            required=False,
        )

    # === REGISTRATION FULL EMAIL ===
    form.fieldset(
            "registrationfullemailsettings",
            label=_(u"Registration Full EMail Settings"),
            fields=[
                'sendRegistrationFullEMail',
                'registrationFullEMailFrom',
                'registrationFullEMailSubject',
                'registrationFullEMailBody'
            ])

    sendRegistrationFullEMail = schema.Bool(
            title=_(u"Send Registration Full EMail"),
            description=_(u"If unchecked, no email indicating registration "
                          u"has reached it's maximum capacity regardless "
                          u"of the number of registrations"),
            required=True,
            default=False,
        )
    registrationFullEMailFrom = schema.TextLine(
            title=_(u"EMail address to send Registration EMail from"),
            description=_(u"The EMail address to use in the From field"),
            required=False,
        )
    registrationFullEMailSubject = schema.TextLine(
            title=_(u"Registration Full EMail Subject"),
            description=_(u"The subject of the EMail sent when the maximum "
                          u"registrations have been reached, and the "
                          u"waiting list has been disabled"),
            required=False,
            default=_(u"We're sorry, but registration is full"),
        )
    registrationFullEMailBody = schema.Text(
            title=_(u"Registration Full EMail Body"),
            description=_(u"The content of the EMail a person receives when "
                          u"registration is full and the waiting list "
                          u"has been disabled"),
            required=False,
            default=_(u"We're sorry, but the event you registered for is "
                      u"full.")
        )

    # === WAITING LIST EMAIL ===
    form.fieldset(
            "waitinglistemailsettings",
            label=_(u"Waiting List EMail Settings"),
            fields=[
                'sendWaitingListEMail',
                'waitingListEMailFrom',
                'waitingListEMailSubject',
                'waitingListEMailBody',
                'offWaitingListEMailSubject',
                'offWaitingListEMailBody'
            ])

    sendWaitingListEMail = schema.Bool(
            title=_(u"Send Waiting List EMail"),
            description=_(u"If unchecked, no email will be sent indicating "
                          u"the person registering has been placed on a "
                          u"waiting list"),
            required=True,
            default=False,
        )
    waitingListEMailFrom = schema.TextLine(
            title=_(u"EMail address to send Waiting List EMail from"),
            description=_(u"The EMail address to use in the From field"),
            required=False,
        )
    waitingListEMailSubject = schema.TextLine(
            title=_(u"Waiting List EMail Subject"),
            description=_(u"The subject of the EMail sent when the number "
                          u"of registrations has reached capacity, but "
                          u"the waiting list is enabled"),
            required=False,
            default=_(u"You have been placed on a waiting list"),
        )
    waitingListEMailBody = schema.Text(
            title=_(u"Waiting List EMail Body"),
            description=_(u"The content of the EMail a person receives when "
                          u"registration is full and they have been put "
                          u"on a waiting list"),
            required=False,
            default=_(u"Unfortunately there are no more open registrations "
                      u"available, but you have been put on a waiting "
                      u"list and will receive another email should a "
                      u"registration become available")
        )
    offWaitingListEMailSubject = schema.TextLine(
            title=_(u"Off Waiting List EMail Subject"),
            description=_(u"When a person has been placed on the waiting "
                          u"list, this is the subject of the email that "
                          u"will be sent to them to complete their "
                          u"registration after another registration has "
                          u"been cancelled"),
            required=False,
            default=_(u"Registration is available"),
        )
    offWaitingListEMailBody = schema.Text(
            title=_(u"Off Waiting List EMail Body"),
            description=_(u"When a person has been placed on the waiting "
                          u"list, this is the content of the email that "
                          u"will be sent to them to complete their "
                          u"registration after another registration has "
                          u"been cancelled"),
            required=False,
            default=_(u"A registration has become available, if you are "
                      u"interested in attending, you can complete your "
                      u"registration by following the instructions below"),
        )


class IEMailSenderForm(interface.Interface):
    pass


class MailBodyTemplate(PageTemplateFile):
    def pt_getContext(self, args=(), options={}, **kw):
        rval = PageTemplateFile.pt_getContext(self, args=args)
        options.update(rval)
        return options


def sendEMail(emevent, emailtype, mto=[], reg=None, attachments=[]):
    mfrom = ''
    msubject = ''
    mbody = ''
    mtemplate = ''

    mh = getToolByName(emevent, 'MailHost')

    if emailtype == 'thank you':
        mfrom = emevent.thankYouEMailFrom
        msubject = emevent.thankYouEMailSubject
        mbody = emevent.thankYouEMailBody
        if emevent.thankYouIncludeConfirmation:
            mtemplate = 'email_thankyou_includeConfirmation.pt'
            attachments.append('attachment1')
        else:
            mtemplate = 'email_thankyou.pt'

    elif emailtype == 'on waiting list':
        mfrom = emevent.waitingListEMailFrom
        msubject = emevent.waitingListEMailSubject
        mbody = emevent.waitingListEMailBody
        mtemplate = 'email_onwaitinglist.pt'

    elif emailtype == 'registration full':
        mfrom = emevent.registrationFullEMailFrom
        msubject = emevent.registrationFullEMailSubject
        mbody = emevent.registrationFullEMailBody
        mtemplate = 'email_registrationfull.pt'

    elif emailtype == 'announcement':
        mfrom = emevent.announcementEMailFrom
        msubject = emevent.announcementEMailSubject
        mbody = emevent.announcementEMailBody
        mtemplate = 'email_announcement.pt'

    elif emailtype == 'confirmation':
        mfrom = emevent.confirmationEMailFrom
        msubject = emevent.confirmationEMailSubject
        mbody = emevent.confirmationEMailBody
        mtemplate = 'email_confirmation.pt'

    if mfrom == None or mfrom == '':
        return False

    template = MailBodyTemplate(mtemplate)
    context = {'mailbody': mbody, 'emevent': emevent, 'reg': reg}
    message = template(context=context)

    for address in mto:
        msg = None
        if attachments != None and len(attachments) > 0:
            msg = MIMEMultipart(message)
            msg['Subject'] = msubject
            msg['From'] = mfrom

            #import pdb; pdb.set_trace()
            #attachment = MIMEBase('maintype', 'subtype')
            #attachment.set_payload(file)
            #encoders.encode_base64(attachment)
            #attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            #msg.attach(attachment)
        else:
            msg = MIMEText(message)
            msg['Subject'] = msubject
            msg['From'] = mfrom

        msg['To'] = address
        mh.send(msg)

    #mh.send('message', 'to@example.com', 'from@example.com', 'subject')

    return True


def canAdd(folder, type_name):
    folder.setConstrainTypesMode(1)
    folder.setLocallyAllowedTypes((BASE_TYPE_NAME + type_name,))


def addSessionsFolder(emevent):
    # add a folder to hold sessions
    id = emevent.invokeFactory('Folder', 'sessions', title="Sessions")
    canAdd(emevent[id], 'Session')


def addSessionCalendarFolder(emevent):
    # add an ATTopic to display a calendar for sessions, if
    # sessions are enabled
    idval = emevent.invokeFactory('Topic', 'session-calendar',
        title="Session Calendar")
    sessioncal = emevent[idval]
    criterion = sessioncal.addCriterion('Type', 'ATPortalTypeCriterion')
    criterion.setValue('Session')
    criterion = sessioncal.addCriterion('path', 'ATRelativePathCriterion')
    criterion.setRelativePath('../sessions')
    sessioncal.setLayout('solgemafullcalendar_view')


@grok.subscribe(IEMEvent, IObjectAddedEvent)
def addFoldersForEventFormsFolder(emevent, event):
    """Adds the forms and folders required for an emevent"""

    # add session container and a session calendar
    if emevent.enableSessions:
        if 'sessions' not in emevent.objectIds():
            addSessionsFolder(emevent)
        if 'session-calendar' not in emevent.objectIds():
            addSessionCalendarFolder(emevent)

    id = emevent.invokeFactory(
                        'Folder',
                        'registrations',
                        title='Registrations')
    canAdd(emevent[id], 'Registration')

    # add a folder to hold travel accommodations
    id = emevent.invokeFactory(
                        'Folder',
                        'travel-accommodations',
                        title='Travel Accommodations')
    canAdd(emevent[id], 'TravelAccommodation')

    # add a folder to hold lodging accommodations
    id = emevent.invokeFactory(
                        'Folder',
                        'lodging-accommodations',
                        title='Lodging Accommodations')
    canAdd(emevent[id], 'LodgingAccommodation')


@grok.subscribe(IEMEvent, IObjectModifiedEvent)
def checkEventForSessionsState(emevent, event):
    """If sessions are disabled then remove the sessions folder,
       they are enabled, then session folders should be added."""
    ids = emevent.objectIds()
    if not emevent.enableSessions:
        if 'sessions' in ids:
            emevent.manage_delObjects(['sessions'])
        if 'session-calendar' in ids:
            emevent.manage_delObjects(['session-calendar'])
    else:
        if 'sessions' not in ids:
            addSessionsFolder(emevent)
        if 'session-calendar' not in ids:
            addSessionCalendarFolder(emevent)


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in event_templates/view.pt
    """

    grok.context(IEMEvent)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)


class EMailSenderForm(BrowserView):
    """Presents a page that allows an event admin to send out
       registraiton and confirmation emails manually"""

    def __call__(self):
        self.emailSent = False
        if self.request.form is not None \
                and len(self.request.form) > 0 \
                and 'submit' in self.request.form:

            emailtype = self.request.form['emailtype']
            tolist = self.request.form['emailtoaddresses'].splitlines()
            if emailtype == 'announcement':
                sendEMail(self.__parent__, 'announcement', tolist)
            elif emailtype == 'confirmation':
                sendEMail(self.__parent__, 'confirmation', tolist)

            self.emailSent = True

        return super(EMailSenderForm, self).__call__()

    def registrationEMailList(self):
        regfolder = self.__parent__.registrations
        return ''.join(["\"%s\" <%s>\n"
                           % (regfolder[reg].title, regfolder[reg].description)
                       for reg in regfolder])

    def showMessageEMailSent(self):
        if getattr(self, 'emailSent', None) != None:
            return self.emailSent

        return False
