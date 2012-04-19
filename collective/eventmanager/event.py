from five import grok
from zope import schema
from plone.directives import form

from plone.namedfile.field import NamedBlobFile
from plone.app.textfield import RichText

from collective.eventmanager import EventManagerMessageFactory as _


class IEMEvent(form.Schema):
    """An event"""

    name = schema.TextLine(
            title=_(u"Event Name"),
            description=_(u"Name of the event as displayed to users"),
            required=True,
        )

    description = schema.Text(
            title=_(u"Description/Notes"),
            description=_(u"Description or notes to be displayed about the "
                            + u"event."),
            required=False,
        )

    startdate = schema.Datetime(
            title=_(u"Start Date/Time"),
            description=_(u"Date and time the Event starts"),
            required=True,
        )

    enddate = schema.Datetime(
            title=_(u"End Date/Time"),
            description=_(u"Date and time the Event ends"),
            required=True,
        )

    registrationOpen = schema.Datetime(
            title=_(u"Registration Open"),
            description=_(u"Date and time registration for the event is open"),
            required=True,
        )

    registrationClosed = schema.Datetime(
            title=_(u"Registration Closed"),
            description=_(u"Date and time registration for the event " \
                            + u"is closed"),
            required=False,
        )

    location = schema.TextLine(
            title=_(u"Location"),
            description=_(u"Address of the location of the event"),
            required=False,
        )

    maxRegistrations = schema.Int(
            title=_(u"Maximum Registrations Available"),
            description=_(u"The maximum amount of registrations to accept "
                            + u"before closing registration, or, if enabled, "
                            + u"putting registrants on a waiting list -- "
                            + u"leave empty for no limit"),
            required=False,
        )

    enableRegistrationList = schema.Bool(
            title=_(u"Enable Waiting List"),
            description=_(u"When enabled, registration will stay open beyond "
                            + u"the maximum registration, but registrants "
                            + u"will be put on a waiting list"),
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
                            + u"registration, check this field"),
            required=True,
            default=False
        )

    privateRegistration = schema.Bool(
            title=_(u"Private Registration"),
            description=_(u"Require that all registration be done manually by "
                            + u"a site administrator"),
            required=True,
            default=False,
        )

    privateEvent = schema.Bool(
            title=_(u"Private Event"),
            description=_(u"Hide the event from the public calendar, potential"
                            + u" registrants must be either added manually or "
                            + u"receive an announcement email containing a "
                            + u"registration link")
        )

    # === ANNOUNCEMENT EMAIL ===
    # sent to a list of email addresses, either manually by an administrator
    # or automatically when registration opens
    sendAnnouncementEMail = schema.Bool(
            title=_(u"Send Announcement EMail Automatically"),
            description=_(u"Send an announcement email when event registration"
                            + u" opens, otherwise an administrator can send"
                            + u" the annoucement email at any time"),
            required=True,
            default=False,
        )
    sendAnnouncementEMailTo = schema.Text(
            title=_(u"EMail addresses to send Announcement to"),
            description=_(u"list of addresses separated by commas or newlines "
                            + u"to send the announcement email to. This field "
                            + u"can be left blank if the announcement will "
                            + u"not be sent automatically"),
            required=False,
        )
    announcementEMailSubject = schema.TextLine(
            title=_(u"Annoucement EMail Subject"),
            description=_(u"The subject of the EMail announcing the event"),
            required=False,
            default=_(u"A New Event is Available"),
        )
    announcementEMailBody = RichText(
            title=_(u"Announcement EMail Body"),
            description=_(u"The content of the EMail announcing the event"),
            required=False,
            default=_(u"")
        )

    # === THANK YOU EMAIL ===
    # this email gets sent as soon as a person has completed registration
    thankYouEMailSubject = schema.TextLine(
            title=_(u"Thank You EMail Subject"),
            description=_(u"The subject of the EMail a person receives after "
                            + u"registering for the event"),
            required=True,
            default=_(u"Registration Complete"),
        )
    thankYouEMailBody = RichText(
            title=_(u"Thank You EMail Body"),
            description=_(u"The content of the EMail a person receives after "
                            + u"registering for the event, NOTE: this message "
                            + u"appears before any registration details, such "
                            + u"as a registration number or cancellation "
                            + u"link"),
            required=True,
            default=_(u"Thank you for registering for this event."),
        )

    # === CONFIRMATION EMAIL ===
    # this email gets sent either automatically on the date/time indicated,
    # or manually by an administrator.
    sendConfirmationEMailAutomatically = schema.Bool(
            title=_(u"Send Confirmation EMail Manually"),
            description=_(u"If checked, a confirmation email will be sent to "
                            + u"everyone registered for the event on the "
                            + u"date/time specified"),
            required=True,
            default=False,
        )
    sendConfirmationEMailOn = schema.Datetime(
            title=_(u"Date/Time to Send Confirmation EMail"),
            description=_(u"If no value is entered, no email will be sent"),
            required=False,
        )
    confirmationEMailSubject = schema.TextLine(
            title=_(u"Confirmation EMail Subject"),
            description=_(u"The subject of the email sent on the confirmation "
                            + u"date and time"),
            required=False,
            default=_(u"Please confirm your registration"),
        )
    confirmationEMailBody = RichText(
            title=_(u"Confirmation EMail Body"),
            description=_(u"The content of the email sent on the confirmation "
                            + u"date and time"),
            required=False,
            default=_(u""),
        )
    confirmationEMailAttachment1 = NamedBlobFile(
            title=_(u"First email attachment"),
            description=_(u"A file attached to the confirmation email"),
            required=False,
        )

    confirmationEMailAttachment2 = NamedBlobFile(
            title=_(u"Second email attachment"),
            description=_(u"A file attached to the confirmation email"),
            required=False,
        )

    confirmationEMailAttachment3 = NamedBlobFile(
            title=_(u"Third email attachment"),
            description=_(u"A file attached to the confirmation email"),
            required=False,
        )

    confirmationEMailAttachment4 = NamedBlobFile(
            title=_(u"Fourth email attachment"),
            description=_(u"A file attached to the confirmation email"),
            required=False,
        )

    # === REGISTRATION FULL EMAIL ===
    sendRegistrationFullEMail = schema.Bool(
            title=_(u"Send Registration Full EMail"),
            description=_(u"If unchecked, no email indicating registration "
                            + u"has reached it's maximum capacity regardless "
                            + u"of the number of registrations"),
            required=True,
            default=False,
        )
    registrationFullEMailSubject = schema.TextLine(
            title=_(u"Registration Full EMail Subject"),
            description=_(u"The subject of the EMail sent when the maximum "
                            + u"registrations have been reached, and the "
                            + u"waiting list has been disabled"),
            required=False,
            default=_(u"We're sorry, but registration is full"),
        )
    registrationFullEMailBody = RichText(
            title=_(u"Registration Full EMail Body"),
            description=_(u"The content of the EMail a person receives when "
                            + u"registration is full and the waiting list "
                            + u"has been disabled"),
            required=False,
            default=_(u"We're sorry, but the event you registered for is "
                        + u"full.")
        )

    # === WAITING LIST EMAIL ===
    sendWaitingListEMail = schema.Bool(
            title=_(u"Send Waiting List EMail"),
            description=_(u"If unchecked, no email will be sent indicating "
                            + u"the person registering has been placed on a "
                            + u"waiting list"),
            required=True,
            default=False,
        )
    waitingListEMailSubject = schema.TextLine(
            title=_(u"Waiting List EMail Subject"),
            description=_(u"The subject of the EMail sent when the number "
                            + u"of registrations has reached capacity, but "
                            + u"the waiting list is enabled"),
            required=False,
            default=_(u"You have been placed on a waiting list"),
        )
    waitingListEMailBody = RichText(
            title=_(u"Waiting List EMail Body"),
            description=_(u"The content of the EMail a person receives when "
                            + u"registration is full and they have been put "
                            + u"on a waiting list"),
            required=False,
            default=_(u"Unfortunately there are no more open registrations "
                        + u"available, but you have been put on a waiting "
                        + u"list and will receive another email should a "
                        + u"registration become available")
        )
    offWaitingListEMailSubject = schema.TextLine(
            title=_(u"Off Waiting List EMail Subject"),
            description=_(u"When a person has been placed on the waiting "
                            + u"list, this is the subject of the email that "
                            + u"will be sent to them to complete their "
                            + u"registration after another registration has "
                            + u"been cancelled"),
            required=False,
            default=_(u"Registration is available"),
        )
    offWaitingListEMailBody = RichText(
            title=_(u"Off Waiting List EMail Body"),
            description=_(u"When a person has been placed on the waiting "
                            + u"list, this is the content of the email that "
                            + u"will be sent to them to complete their "
                            + u"registration after another registration has "
                            + u"been cancelled"),
            required=False,
            default=_(u"A registration has become available, if you are "
                        + u"interested in attending, you can complete your "
                        + u"registration by following the instructions below"),
        )


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in event_templates/view.pt
    """

    grok.context(IEMEvent)
    grok.require('zope2.View')
    grok.name('view')
