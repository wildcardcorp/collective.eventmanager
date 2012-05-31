import string

from five import grok
from zope import schema, interface
from plone.directives import form
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from plone.namedfile.field import NamedBlobFile
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarMarker
from datetime import datetime
from Products.CMFCore.utils import getToolByName
from mako.template import Template
from Products.Five.browser import BrowserView
from plone.protect import protect, CheckAuthenticator
from collective.geo.mapwidget.browser.widget import MapWidget
from collective.z3cform.mapwidget.widget import MapFieldWidget
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

from collective.eventmanager.config import BASE_TYPE_NAME
from collective.eventmanager.interfaces import ILayer
from collective.eventmanager import EventManagerMessageFactory as _
from collective.eventmanager.vocabularies import \
    RegistrationRowAvailableFieldTypes


class IRegistrationFieldRow(interface.Interface):
    name = schema.TextLine(
            title=u"Name",
            required=True,
        )

    fieldtype = schema.Choice(
            title=u"Field Type",
            vocabulary=RegistrationRowAvailableFieldTypes,
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
                'sendOffWaitingListEMail',
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
    sendOffWaitingListEMail = schema.Bool(
            title=_(u"Send EMail When Registration Moves off Waiting List"),
            description=_(u"When an admin moves a registration from the "
                          u"waiting list to be either approved or "
                          u"confirmed, the 'off waiting list' email is "
                          u"sent if this option is checked"),
            required=False,
            default=False
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


class IRegistrationStatusForm(interface.Interface):
    pass


def sendEMail(emevent, emailtype, mto=[], reg=None, defattachments=[],
              deffrom=None, defsubject=None, defmsg=None):
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

            #import pdb; pdb.set_trace()
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


def _canAdd(folder, type_name):
    folder.setConstrainTypesMode(1)
    folder.setLocallyAllowedTypes((BASE_TYPE_NAME + type_name,))


def _addSessionsFolder(emevent):
    # add a folder to hold sessions
    id = emevent.invokeFactory('Folder', 'sessions', title="Sessions")
    _canAdd(emevent[id], 'Session')


def _addSessionCalender(emevent):
    # Add a collections object for a calendar if available.
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
            _addSessionsFolder(emevent)
        if 'session-calendar' not in emevent.objectIds():
            _addSessionCalender(emevent)

    id = emevent.invokeFactory(
                        'Folder',
                        'registrations',
                        title='Registrations')
    _canAdd(emevent[id], 'Registration')

    # add a folder to hold travel accommodations
    id = emevent.invokeFactory(
                        'Folder',
                        'travel-accommodations',
                        title='Travel Accommodations')
    _canAdd(emevent[id], 'Accommodation')

    # add a folder to hold lodging accommodations
    id = emevent.invokeFactory(
                        'Folder',
                        'lodging-accommodations',
                        title='Lodging Accommodations')
    _canAdd(emevent[id], 'Accommodation')


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
            _addSessionsFolder(emevent)
        if 'session-calendar' not in ids:
            _addSessionCalender(emevent)


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in event_templates/view.pt
    """

    grok.context(IEMEvent)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)

    MAP_CSS_CLASS = 'eventlocation'

    def __call__(self):
        # setup map widget
        portal = getToolByName(self.context, "portal_url")
        mw = MapWidget(self, self.request, portal)
        mw.mapid = self.MAP_CSS_CLASS
        mw.addClass(self.MAP_CSS_CLASS)
        self.mapfields = [mw]

        return super(View, self).__call__()

    @property
    def number_registered(self):
        # XXX Optimize! catalog
        registrationfolder = self.context.registrations
        wftool = getToolByName(self.context, "portal_workflow")
        count = 0
        for reg in registrationfolder.objectValues():
            status = wftool.getStatusOf(
                "collective.eventmanager.Registration_workflow", reg)
            if status['review_state'] in ('approved', 'confirmed'):
                count += 1
        return count

    @property
    def number_wait_list(self):
        # XXX Optimize! catalog
        registrationfolder = self.context.registrations
        wftool = getToolByName(self.context, "portal_workflow")
        count = 0
        for reg in registrationfolder.objectValues():
            status = wftool.getStatusOf(
                "collective.eventmanager.Registration_workflow", reg)
            if status['review_state'] in ('submitted',):
                count += 1
        return count

    def getRegistration(self):
        mt = getToolByName(self.context, 'portal_membership')
        if mt.isAnonymousUser():
            return False
        # XXX should be optimized
        member = mt.getAuthenticatedMember()
        username = member.getUserName()
        registrationfolder = self.context.registrations
        for reg in registrationfolder.objectValues():
            if reg.email == username:
                return reg

    @property
    def registered(self):
        reg = self.getRegistration()
        if reg is None:
            return False
        return True

    @property
    def waiting_list(self):
        reg = self.getRegistration()
        if reg is None:
            return False
        wftool = getToolByName(self.context, "portal_workflow")
        status = wftool.getStatusOf(
            "collective.eventmanager.Registration_workflow", reg)
        return status['review_state'] != 'approved'


    def cgmapSettings(self):
        settings = {}

        coords = [0, 0]
        if self.context.location != None \
                and self.context.location[0:6] == u'POINT(':
            coords = string.split(self.context.location[6:-1], ' ')

        settings['lon'] = float(coords[0])
        settings['lat'] = float(coords[1])
        settings['zoom'] = 16

        return "cgmap.state['" + self.MAP_CSS_CLASS + "'] = " \
               + str(settings) + ";"


class EMailSenderForm(BrowserView):
    """Presents a page that allows an event admin to send out
       registraiton and confirmation emails manually"""

    def __call__(self):
        self.emailSent = False
        if self.request.form is not None \
                and len(self.request.form) > 0 \
                and 'submit' in self.request.form:

            self._handlePost(self.request)

        return super(EMailSenderForm, self).__call__()

    @protect(CheckAuthenticator)
    def _handlePost(self, REQUEST=None):
        emailtype = REQUEST.form['emailtype']
        tolist = REQUEST.form['emailtoaddresses'].splitlines()
        attachments = []
        if REQUEST.form['attachment1'].filename != '':
            attachments.append({
                'name': REQUEST.form['attachment1'].filename,
                'data': REQUEST.form['attachment1'].read()})
        if REQUEST.form['attachment2'].filename != '':
            attachments.append({
                'name': REQUEST.form['attachment2'].filename,
                'data': REQUEST.form['attachment2'].read()})
        if REQUEST.form['attachment3'].filename != '':
            attachments.append({
                'name': REQUEST.form['attachment3'].filename,
                'data': REQUEST.request.form['attachment3'].read()})
        if REQUEST.form['attachment4'].filename != '':
            attachments.append({
                'name': REQUEST.form['attachment4'].filename,
                'data': REQUEST.form['attachment4'].read()})
        mfrom = REQUEST.form['emailfromaddress']
        msubject = REQUEST.form['emailsubject']
        mbody = REQUEST.form['emailbody']
        sendEMail(self.__parent__, emailtype, tolist, None, attachments,
                  mfrom, msubject, mbody)

        self.emailSent = True

    def registrationEMailList(self):
        regfolder = self.__parent__.registrations
        return ''.join(["\"%s\" <%s>\n"
                           % (regfolder[reg].title, regfolder[reg].description)
                       for reg in regfolder])

    def showMessageEMailSent(self):
        if getattr(self, 'emailSent', None) != None:
            return self.emailSent

        return False

    def confirmationFrom(self):
        return self.__parent__.thankYouEMailFrom

    def confirmationSubject(self):
        return self.__parent__.thankYouEMailSubject

    def confirmationBody(self):
        return self.__parent__.thankYouEMailBody


class RegistrationStatusForm(BrowserView):
    """Creates a form that an event adminsitrator can manage registrations
    currently on the waiting list"""

    def __call__(self):
        if self.request.form is not None \
                and len(self.request.form) > 0 \
                and 'submit' in self.request.form:

            self._handlePost(self.request)

        return super(RegistrationStatusForm, self).__call__()

    @protect(CheckAuthenticator)
    def _handlePost(self, REQUEST):
        subtype = REQUEST.form['submit']
        idlist_submitted = self._getActionsFor('submitted', REQUEST)
        idlist_approved = self._getActionsFor('approved', REQUEST)
        idlist_confirmed = self._getActionsFor('confirmed', REQUEST)
        idlist_cancelled = self._getActionsFor('cancelled', REQUEST)
        idlist_denied = self._getActionsFor('denied', REQUEST)

        if subtype == 'Wait List':
            self._doActions(idlist_approved, ['cancel', 'modify'])
            self._doActions(idlist_confirmed, ['cancel', 'modify'])
            self._doActions(idlist_cancelled, ['modify'])
            self._doActions(idlist_denied, ['modify'])
        elif subtype == 'Approve':
            sendm = self.__parent__.sendOffWaitingListEMail
            self._doActions(idlist_submitted, ['approve'], sendm)
            self._doActions(idlist_confirmed, ['cancel', 'approve'])
            self._doActions(idlist_cancelled, ['approve'])
            self._doActions(idlist_denied, ['approve'])
        elif subtype == 'Confirm':
            sendm = self.__parent__.sendOffWaitingListEMail
            self._doActions(idlist_submitted, ['approve', 'confirm'], sendm)
            self._doActions(idlist_approved, ['confirm'])
            self._doActions(idlist_cancelled, ['approve', 'confirm'])
            self._doActions(idlist_denied, ['approve', 'confirm'])
        elif subtype == 'Cancel':
            self._doActions(idlist_submitted, ['cancel'])
            self._doActions(idlist_approved, ['cancel'])
            self._doActions(idlist_confirmed, ['cancel'])
            self._doActions(idlist_denied, ['cancel'])
        elif subtype == 'Deny':
            self._doActions(idlist_submitted, ['deny'])
            self._doActions(idlist_approved, ['deny'])
            self._doActions(idlist_confirmed, ['deny'])
            self._doActions(idlist_cancelled, ['deny'])
            pass

    def _getActionsFor(self, actiontype, REQUEST):
        if actiontype in REQUEST.form:
            if type(REQUEST.form[actiontype]) == list:
                return REQUEST.form[actiontype]
            else:
                return [REQUEST.form[actiontype]]

        return []

    def _doActions(self, idlist=[], actions=[], sendwaitlistemail=False):
        for id in idlist:
            reg = self.__parent__.registrations[id]
            wf = getToolByName(reg, "portal_workflow")
            for action in actions:
                wf.doActionFor(reg, action)
            if sendwaitlistemail:
                mfrom = self.__parent__.waitingListEMailFrom
                mto = reg.description
                msubject = self.__parent__.offWaitingListEMailSubject
                mbody = self.__parent__.offWaitingListEMailBody
                mh = getToolByName(self.__parent__, 'MailHost')
                mh.send(mbody, mto, mfrom, msubject)

    def getRegistrationsWithStatus(self, status):
        wf = getToolByName(self, 'portal_workflow')
        wfstr = "collective.eventmanager.Registration_workflow"
        items = [r for r in self.__parent__.registrations]
        registrations = []
        for reg in items:
            regstatus = wf.getStatusOf(wfstr,
                                       self.__parent__.registrations[reg])
            reviewstate = regstatus['review_state']
            if reviewstate != None \
                    and reviewstate.lower() == status.lower():
                registrations.append(self.__parent__.registrations[reg])

        return registrations

