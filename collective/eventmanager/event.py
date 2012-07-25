from datetime import datetime

from zope import schema
from zope.interface import Interface
from plone.directives import form
from plone.namedfile.field import NamedBlobFile
from plone.app.textfield import RichText
from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarMarker
from collective.z3cform.mapwidget.widget import MapFieldWidget
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow

from collective.eventmanager import EventManagerMessageFactory as _
from collective.eventmanager.vocabularies import \
    RegistrationRowAvailableFieldTypes


class IRegistrationFieldRow(Interface):
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
    configuration = schema.Text(
            title=u"Field Configuration",
            required=False,
        )

    configuration = schema.Text(
        title=u"Configuration",
        required=False)


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

    registrationFee = schema.Float(
            title=_(u"Registration Fee"),
            description=_(u"Fee to register for event. Leave at 0 if no fee."),
            required=True,
            default=0.0
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

    body = RichText(
            title=_(u"Body"),
            description=_(u"This field describes additional content of an "
                          u"event"),
            required=False,
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
            label=_(u"Thank You/Confirmation EMail Settings"),
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

