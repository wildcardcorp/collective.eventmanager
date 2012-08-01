from Acquisition import aq_base
from datetime import datetime
from email import message_from_string
from plone.testing.z2 import Browser
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost
from StringIO import StringIO
import transaction
import unittest2 as unittest
from zope.component import getSiteManager

from collective.eventmanager.registration import generateRegistrationHash
from collective.eventmanager.tests import BaseTest
from collective.eventmanager.testing import browserLogin


class TestViews(BaseTest):

    def setUp(self):
        super(TestViews, self).setUp()
        self.browser = Browser(self.layer['app'])
        self.browser.handleErrors = False
        self.portal_url = self.portal.absolute_url()

        self.setUpMailHost()

    def tearDown(self):
        super(TestViews, self).tearDown()

        self.tearDownMailHost()

    def setUpMailHost(self):
        # setup mock mailhost
        self.portal._original_MailHost = self.portal.MailHost
        self.portal.MailHost = mailhost = MockMailHost('MailHost')
        sm = getSiteManager(context=self.portal)
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(mailhost, provided=IMailHost)
        transaction.commit()

    def tearDownMailHost(self):
        self.portal.MailHost = self.portal._original_MailHost
        sm = getSiteManager(context=self.portal)
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(aq_base(self.portal._original_MailHost),
                           provided=IMailHost)

    def registerNewUser(self, event, name, email, noshow=True):
        self.browser.open(event.absolute_url() + \
            '/registrations/++add++collective.eventmanager.Registration')
        self.browser.getControl(name="form.widgets.title").value = name
        self.browser.getControl(name="form.widgets.email").value = email
        self.browser.getControl('Register').click()

        # this is a hack -- the 'noshow' widget is a hidden field by default
        # and only accepts 'selected' as value, so if noshow==False, then
        # we can just set the value in the newly create registration
        for r in [event.registrations[a] for a in event.registrations]:
            if r.title == name:
                r.noshow = noshow
                break

    def getLastEvent(self, evid):
        return self.portal[[a for a in self.portal
                               if a[:10] == evid][-1]]

    def test_searchable_public_training_calendar(self):
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl('Save').click()
        self.browser.getLink('Publish').click()
        self.browser.open(self.portal_url + '/logout')
        self.browser.open(self.portal_url + \
            '/@@search?SearchableText=Test Event')
        assert '<dt class="contenttype-collective-eventmanager-emevent">' in \
            self.browser.contents

    def test_calendar_includes_name_location_link_etc(self):
        # the values that should be on an item linked to by a calendar
        # (assuming the appropriate options are enabled):
        #   - name
        #   - location
        #   - registration link
        #   - seats remaining
        #   - registration start date
        #   - flyer link
        #   - notes

        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')

        # set name, location, max registrations, flyer, and body/notes element
        # -- the registration link should be auto generated, and the
        #    registration start date should be defaulted to the current day
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl(
            'Description/Notes').value = 'Event Description'
        self.browser.getControl(
            name='form.widgets.location').value = 'POINT(-100.0,100.0)'
        self.browser.getControl(
            name='form.widgets.maxRegistrations').value = '2'
        self.browser.getControl(name='form.widgets.flyer') \
            .add_file(StringIO('test file'),
                      'text/plain',
                      'test.txt')
        self.browser.getControl(
            name='form.widgets.body').value = 'Body Content'

        self.browser.getControl('Save').click()
        newevt = self.getLastEvent('test-event')

        # add a registration
        self.registerNewUser(newevt, "Test Registration", "test@foo.bar")

        # inspect the event page
        self.browser.open(newevt.absolute_url())

        assert '>Test Event</h1>' in self.browser.contents
        assert 'id="map"' in self.browser.contents
        assert '>Register for this event</a>' in self.browser.contents

        assert 'class="num">1</span>' in self.browser.contents \
                and 'of 2' in self.browser.contents
        assert 'Registration opens <span>%s' \
                    % (datetime.now().strftime('%A, %x at ')) \
                in self.browser.contents
        assert 'href="./@@display-file/flyer"' in self.browser.contents
        assert 'Body Content' in self.browser.contents

    def test_customizable_registration_form(self):
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        # XXX not working without js?
        # XXX    -> seems to still function correctly when javascript is
        #           disabled - is it not pulling data from a correct layer?
        self.browser.getControl(
            name='form.widgets.registrationFields.AA.widgets.name'
            ).value = 'Custom Field'
        self.browser.getControl(
            name="form.widgets.registrationFields.AA.widgets.fieldtype:list"
            ).value = ['TextLine']
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')
        self.browser.open(event.absolute_url() + \
            '/registrations/++add++collective.eventmanager.Registration')
        assert "Custom Field" in self.browser.contents

    def test_registration_is_closed_when_full_and_no_waitlist(self):
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(
            name="form.widgets.maxRegistrations").value = "2"
        #import pdb; pdb.set_trace()
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')
        self.registerNewUser(event, 'test1', 'test1@foobar.com')
        self.registerNewUser(event, 'test2', 'test2@foobar.com')
        self.browser.open(event.absolute_url())
        #import pdb; pdb.set_trace()
        assert "Registration is closed" in self.browser.contents

    def test_registration_is_closed_on_dates_closed(self):
        browserLogin(self.portal, self.browser)

        def setEventDates(widgetbase, dayadj, houradj):
            self.browser.getControl(name='%s-day' % (widgetbase,)) \
                .value = str(datetime.now().day + dayadj)
            self.browser.getControl(name='%s-month' % (widgetbase,)) \
                .value = [str(datetime.now().month)]
            self.browser.getControl(name='%s-year' % (widgetbase,)) \
                .value = str(datetime.now().year)
            self.browser.getControl(name='%s-hour' % (widgetbase,)) \
                .value = str(datetime.now().hour + houradj)
            self.browser.getControl(name='%s-min' % (widgetbase,)) \
                .value = str(datetime.now().minute)

        def createEvent(houropenadj, hourcloseadj):
            self.browser.open(self.portal_url + \
                '/++add++collective.eventmanager.EMEvent')
            self.browser.getControl('Event Name').value = 'Test Event'
            self.browser.getControl('Description/Notes').value = 'Event desc'

            # set the open date to yesterday and the close date to
            # today -- but one hour in the future
            setEventDates('form.widgets.registrationOpen', -1, houropenadj)
            setEventDates('form.widgets.registrationClosed', 0, hourcloseadj)

            self.browser.getControl('Save').click()
            event = self.getLastEvent('test-event')

            return event

        # get event with a closed time in the future and test to make
        # sure registration is open
        event = createEvent(0, 1)
        self.browser.open(event.absolute_url())
        assert "Registration is closed" not in self.browser.contents

        # get event with a closed time in the past and test to make
        # sure registration is closed
        event = createEvent(0, -1)
        self.browser.open(event.absolute_url())
        assert "Registration is closed" in self.browser.contents

    def test_registration_is_open_with_waitlist(self):
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(
            name="form.widgets.maxRegistrations").value = "2"
        self.browser.getControl(
            name="form.widgets.enableWaitingList:list"
        ).controls[0].selected = True
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')
        self.registerNewUser(event, 'test1', 'test1@foobar.com')
        self.registerNewUser(event, 'test2', 'test2@foobar.com')
        self.browser.open(event.absolute_url())
        assert "Registration is closed" not in self.browser.contents

    def test_registrants_receive_confirmation_email_on_signup(self):
        # create em event
        # enable 'Include Confirmation Link and Message' in the Thank You EMail
        #   settings section
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(
            name="form.widgets.maxRegistrations").value = "2"
        self.browser.getControl(
                name="form.widgets.thankYouIncludeConfirmation:list"
            ).value = 'on'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # add registration
        self.registerNewUser(event, "Test Registration 1", "test1@foobar.com")

        # check captured messages in the mailhost to verify an email with
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages), 1)
        msg = message_from_string(mailhost.messages[0])

        self.assertEqual(msg['To'], 'test1@foobar.com')
        self.assertEqual(
            msg['Subject'],
            self.portal['test-event'].thankYouEMailSubject)
        #self.assertIn(confirmationURL,
        #              self.portal_url + '/test-event/')

        # XXX a confirmation message and link are present
        # TODO: add confirmation message and link to registration email

    def test_registrants_can_cancel(self):
        # setup event
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(
                name='form.widgets.thankYouIncludeConfirmation:list'
            ).value = 'on'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # add registration
        self.registerNewUser(
                event,
                "Test Registration Cancel",
                "testcancel@foobar.com")

        # send confirmation email
        self.browser.open("%s/%s/@@emailsenderform"
                                % (self.portal_url, event.getId()))
        self.browser.getControl(name='emailfromaddress').value = 'tes@tes.com'
        self.browser.getControl(name='emailtoaddresses') \
                    .value = "testcancel@foobar.com"
        self.browser.getControl(name='submit').click()

        # get cancellation link from email
        mailhost = self.portal.MailHost
        assert len(mailhost.messages) == 1
        msg = message_from_string(mailhost.messages[0])
        assert 'testcancel@foobar.com' in msg['To']
        cancelurl = "%s/%s/cancel-registration?h=%s" \
                        % (self.portal_url,
                           event.getId(),
                           generateRegistrationHash(
                                "cancel",
                                event.registrations['test-registration-cancel']
                                ))
        assert cancelurl in mailhost.messages[0]

        # go to cancellation link
        self.browser.open(cancelurl)
        assert "Registration Cancelled" in self.browser.contents

        # assert state of registration is cancelled
        wf = getToolByName(self.portal, "portal_workflow")
        regstatus = wf.getStatusOf(
            'collective.eventmanager.Registration_workflow',
            event.registrations['test-registration-cancel'])
        assert regstatus['review_state'] == 'cancelled'

    def test_waiting_list(self):
        # create event, setting size to 0, forcing all registrations to
        #   waiting list
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(
            name="form.widgets.maxRegistrations").value = "0"
        self.browser.getControl(
            name="form.widgets.enableWaitingList:list").value = "on"
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # add registration
        self.registerNewUser(
                event,
                "Test Registration Waiting List",
                "test@foobar.com")

        # assert registration is 'submitted'
        wf = getToolByName(self.portal, "portal_workflow")
        status = wf.getStatusOf(
            'collective.eventmanager.Registration_workflow',
            event.registrations['test-registration-waiting-list'])
        assert status['review_state'] == 'submitted'

        # go to registration status page
        self.browser.open("%s/%s/@@registrationstatusform"
                            % (self.portal_url,
                               event.getId()))

        # assert registration is listed under 'On Waiting List'
        assert 'Test Registration Waiting List' in self.browser.contents
        assert 'There are no registrations on the waiting list.' \
                    not in self.browser.contents

        # move registration from waiting list to approved
        self.browser.getControl(
                name='submitted'
            ).value = "on"
        self.browser.getControl('Approve').click()

        # assert registration is 'approved'
        status = wf.getStatusOf(
            'collective.eventmanager.Registration_workflow',
            event.registrations['test-registration-waiting-list'])
        assert status['review_state'] == 'approved'

    def test_require_payment(self):
        pass

    def test_registration_info_can_be_managed_by_admins(self):
        # add event
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(
            name="form.widgets.maxRegistrations").value = "0"
        self.browser.getControl(
            name="form.widgets.enableWaitingList:list").value = "on"
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # add registration (admin adds registration)
        self.registerNewUser(
                event,
                "Test Registration",
                "test@foobar.com")

        # assert registration exists
        assert 'test-registration' in event.registrations

        # alter registration name and email (admin doing this)
        self.browser.open("%s/%s/registrations/test-registration/edit"
                            % (self.portal_url,
                               event.getId()))
        self.browser.getControl(name="form.widgets.title") \
                    .value = "New Title Value"
        self.browser.getControl(name="form.widgets.email") \
                    .value = "new@email.com"
        self.browser.getControl(name="form.widgets.noshow:list") \
                    .value = "on"
        self.browser.getControl(name="form.widgets.paid_fee:list") \
                    .value = "on"
        self.browser.getControl("Save").click()

        # assert registration information has changed
        assert 'New Title Value' in self.browser.contents
        assert 'new@email.com' in self.browser.contents
        assert event.registrations['test-registration'].noshow
        assert event.registrations['test-registration'].paid_fee

    def test_post_training_data(self):
        oldbody = "some test body text"
        newbody = "a different value"

        # create event
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(name='form.widgets.body').value = oldbody
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # modify body -- adding files and such is a function of
        #   plone itself, so there's no need to test this, as it
        #   should already be covered in tests.
        self.browser.open(self.portal_url + '/' + event.getId() + '/@@edit')
        self.browser.getControl(name='form.widgets.body').value = newbody
        self.browser.getControl("Save").click()

        # assert that body structure has changed.
        assert oldbody not in self.browser.contents
        assert newbody in self.browser.contents

    def test_send_training_emails(self):
        # create event
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(
            name="form.widgets.maxRegistrations").value = "0"
        self.browser.getControl(
            name="form.widgets.enableWaitingList:list").value = "on"
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # create registrant
        self.registerNewUser(
                event,
                "Test Registration",
                "test@foobar.com")

        # use email sender form to send 'other' email with attachment
        self.browser.open("%s/%s/@@emailsenderform"
                            % (self.portal_url,
                               event.getId()))
        self.browser.getControl(name='emailtype').value = ['other']
        self.browser.getControl(name='emailfromaddress').value = 'test@tes.com'
        self.browser.getControl(name='emailtoaddresses') \
                    .value = 'test@foobar.com'
        self.browser.getControl(name='emailsubject') \
                    .value = 'Training EMail'
        self.browser.getControl(name='emailbody') \
                    .value = 'This is some training material'
        self.browser.getControl(name='attachment1') \
                    .add_file(StringIO('test file'),
                              'text/plain',
                              'test.txt')
        self.browser.getControl(name='submit').click()

        # assert an email was sent with an attachment
        mailhost = self.portal.MailHost
        assert len(mailhost.messages) == 1
        msg = message_from_string(mailhost.messages[0])

        assert msg['To'] == 'test@foobar.com'
        assert msg['Subject'] == "Training EMail"
        assert 'This is some training material' in mailhost.messages[0]
        assert 'Content-Disposition: attachment; filename="test.txt"' \
                    in mailhost.messages[0]

    def test_create_event(self):
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl('Save').click()
        self.assertEqual('test-event' in self.portal, True)
        self.assertEqual(self.portal['test-event'] != None, True)

    def test_clone_event(self):
        # create an event
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event for copy'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # copy the event
        #eventurl = "%s/%s/object_copy" % (self.portal_url, event.getId())
        #import pdb; pdb.set_trace()
        #self.browser.open(eventurl)
        self.browser.open(self.portal_url + '/folder_contents')
        self.browser.getControl('Test Event for copy').selected = True
        self.browser.getControl('Copy').click()
        self.browser.getControl('Paste').click()

        # assert both the old and new event's exist and have the same title
        copyid = 'copy_of_%s' % (event.getId(),)
        assert copyid in self.portal
        eventcopy = self.portal[copyid]
        assert event.title == eventcopy.title

    def test_set_event_dates(self):
        # create an event
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event for copy'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(name='form.widgets.start-day').value = '26'
        self.browser.getControl(name='form.widgets.start-month').value = ['1']
        self.browser.getControl(name='form.widgets.start-year').value = '2002'
        self.browser.getControl(name='form.widgets.start-hour').value = '6'
        self.browser.getControl(name='form.widgets.start-min').value = '34'
        self.browser.getControl(name='form.widgets.end-day').value = '27'
        self.browser.getControl(name='form.widgets.end-month').value = ['1']
        self.browser.getControl(name='form.widgets.end-year').value = '2002'
        self.browser.getControl(name='form.widgets.end-hour').value = '7'
        self.browser.getControl(name='form.widgets.end-min').value = '35'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # go to event page and assert that dates are set
        eventurl = "%s/%s" % (self.portal_url, event.getId())
        self.browser.open(eventurl)
        assert '01/26/02 at 06:34' in self.browser.contents
        assert '01/27/02 at 07:35' in self.browser.contents

        # change the dates to make an all day event
        self.browser.open(eventurl + '/edit')
        self.browser.getControl(name='form.widgets.start-day').value = '26'
        self.browser.getControl(name='form.widgets.start-month').value = ['1']
        self.browser.getControl(name='form.widgets.start-year').value = '2002'
        self.browser.getControl(name='form.widgets.start-hour').value = '6'
        self.browser.getControl(name='form.widgets.start-min').value = '34'
        self.browser.getControl(name='form.widgets.end-day').value = '26'
        self.browser.getControl(name='form.widgets.end-month').value = ['1']
        self.browser.getControl(name='form.widgets.end-year').value = '2002'
        self.browser.getControl(name='form.widgets.end-hour').value = '6'
        self.browser.getControl(name='form.widgets.end-min').value = '34'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # check the event page for all day event
        self.browser.open(eventurl)
        assert 'This is an all day event taking place on' \
                    in self.browser.contents
        assert '01/26/02' in self.browser.contents

    def test_modify_email_templates(self):
        # create an event and registration
        # enable 'Include Confirmation Link and Message' in the Thank You EMail
        #   settings section
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(
            name="form.widgets.maxRegistrations").value = "1"
        self.browser.getControl(
                name="form.widgets.thankYouIncludeConfirmation:list"
            ).value = 'on'
        self.browser.getControl(name='form.widgets.enableWaitingList:list') \
                    .value = "on"
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # add registration
        self.registerNewUser(event, "Test Registration 1", "test1@foobar.com")

        # go to site setup and modify every template
        self.browser.open(self.portal_url + '/@@em-email-templates')

        def setControls(name):
            subjectname = 'form.widgets.%s_subject' % (name,)
            htmlname = 'form.widgets.%s_htmlbody' % (name,)
            textname = 'form.widgets.%s_textbody' % (name,)
            self.browser.getControl(name=subjectname).value = "Test Subject"
            self.browser.getControl(name=htmlname).value = "Test HTML Body"
            self.browser.getControl(name=textname).value = "Test Text Body"

        setControls('announcement')
        setControls('confirmation')
        setControls('onwaitinglist')
        setControls('other')
        setControls('registrationfull')
        setControls('thankyou')
        self.browser.getControl('Save').click()

        emailsenderurl = "%s/%s/@@emailsenderform" \
                            % (self.portal_url, event.getId())

        def checkMailHost():
            mailhost = self.portal.MailHost
            assert len(mailhost.messages) > 0
            msg = message_from_string(mailhost.messages[-1])

            assert msg['Subject'] == 'Test Subject'
            assert 'Test Subject' in mailhost.messages[-1]
            assert 'Test HTML Body' in mailhost.messages[-1]
            assert 'Test Text Body' in mailhost.messages[-1]

        def emailSenderTest(url, emailtype):
            # send the email, since we hard-coded the templates, setting
            # subject and message shouldn't matter here
            self.browser.open(url)
            self.browser.getControl(name='emailtype').value = [emailtype]
            self.browser.getControl(name='emailfromaddress') \
                        .value = 'test@tes.com'
            self.browser.getControl(name='emailtoaddresses') \
                        .value = 'test1@foobar.com'
            self.browser.getControl(name='submit').click()

            # check to see if the content of the email is correct
            checkMailHost()

        # test announcement
        emailSenderTest(emailsenderurl, 'announcement')

        # test confirmation
        emailSenderTest(emailsenderurl, 'confirmation')

        # test on waiting list
        self.registerNewUser(event, "Test Registration 2", "test2@foobar.com")
        checkMailHost()

        # test other
        emailSenderTest(emailsenderurl, 'other')

        # test registration full
        evediturl = "%s/%s/edit" % (self.portal_url, event.getId())
        self.browser.open(evediturl)
        self.browser.getControl(name='form.widgets.enableWaitingList:list') \
                    .value = ""
        self.browser.getControl('Save').click()
        self.registerNewUser(event, "Test Registration 3", "test3@foobar.com")
        checkMailHost()

        # test thank you
        evediturl = "%s/%s/edit" % (self.portal_url, event.getId())
        self.browser.open(evediturl)
        self.browser.getControl(name="form.widgets.maxRegistrations") \
                    .value = "20"
        self.browser.getControl('Save').click()
        self.registerNewUser(event, "Test Registration 4", "test4@foobar.com")
        checkMailHost()

    def test_add_registrations_manually(self):
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        self.registerNewUser(
                event,
                "Test Registration",
                "test@foobar.com")

        assert 'test-registration' in event.registrations

    def test_private_event_and_send_invitations_via_email(self):
        # create private event
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl(name='form.widgets.privateEvent:list') \
                    .value = "on"
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # send announcement email through email sender with link
        #   to registration page
        senderurl = "%s/%s/@@emailsenderform" \
                        % (self.portal_url, event.getId())
        self.browser.open(senderurl)
        self.browser.getControl(name='emailtype').value = ['announcement']
        self.browser.getControl(name='emailfromaddress').value = "test@tes.tes"
        self.browser.getControl(name='emailtoaddresses') \
                    .value = "foo@bar.com"
        self.browser.getControl(name='emailbody').value = """This is an example.
The registration link would be:

http://<your domain>/path/to/your/event/registration-form
        """
        self.browser.getControl(name='submit').click()

        # assert an email with a register link has been sent
        mailhost = self.portal.MailHost
        assert len(mailhost.messages) > 0
        assert '/registration-form' in mailhost.messages[-1]

    def test_ability_to_search_events(self):
        # create event
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # go to search url
        searchurl = self.portal_url + "/@@search?SearchablText=Test+Event"
        self.browser.open(searchurl)

        # assert event in list
        assert 'Test Event' in self.browser.contents

    def test_checkin_roster(self):
        # create event
        browserLogin(self.portal, self.browser)
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # add registration, make sure it's confirmed and not marked
        #   as a no-show
        self.registerNewUser(
            event,
            "Checkin Registration",
            "test@address.com",
            False)
        #self.browser.open(event.absolute_url() + \
        #    '/registrations/++add++collective.eventmanager.Registration')
        #self.browser.getControl(name="form.widgets.title").value = \
        #                                                'Checkin Registration'
        #self.browser.getControl(name="form.widgets.email").value = \
        #                                                'test@address.com'
        #self.browser.getControl(name="form.widgets.noshow:list").value = ""
        #self.browser.getControl(name="form.buttons.register").click()

        #import pdb; pdb.set_trace()

        # goto /@@eventroster and assert that there is at least one
        #   checkbox for the registration (indicating they are not no-shows)
        rosterurl = "%s/%s/@@eventroster" % (self.portal_url,
                                             event.getId())
        self.browser.open(rosterurl)
        assert 'registration="checkin-registration"' in self.browser.contents

    def test_export_registration(self):
        pass

    def test_view_waiting_list(self):
        pass

    def test_reorder_waiting_list(self):
        pass

    def test_email_roster_to_3rd_party(self):
        browserLogin(self.portal, self.browser)

        # create em event
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # add a couple of registrations
        self.registerNewUser(event, "Reg1", "reg1@foobar.com")
        self.registerNewUser(event, "Reg2", "reg1@foobar.com")

        # send roster email
        self.browser.open(self.portal_url + \
            '/test-event/@@eventroster')

        # wrapped in try/except to make sure tear down happens on
        # the mailhost
        self.browser.getControl(
            name='event_roster_email_from').value = 'testfrom@foobar.com'
        self.browser.getControl(
            name='event_roster_email_to').value = 'testto@foobar.com'
        self.browser.getControl(
            name='event_roster_email_text').value = 'test additional text'
        self.browser.getControl(name='event_roster_email_submit').click()

        # check captured messages in the mailhost to verify an email was
        # sent to the to email address
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages) > 0, True)
        msg = message_from_string(
                mailhost.messages[-1])

        self.assertEqual(msg['From'], 'testfrom@foobar.com')
        self.assertEqual(msg['To'], 'testto@foobar.com')

    def test_send_certificate_on_completion(self):
        browserLogin(self.portal, self.browser)

        # create em event
        self.browser.open(self.portal_url + \
            '/++add++collective.eventmanager.EMEvent')
        self.browser.getControl('Event Name').value = 'Test Event'
        self.browser.getControl('Description/Notes').value = 'Event desc'
        self.browser.getControl('Save').click()
        event = self.getLastEvent('test-event')

        # add a registration
        self.registerNewUser(event, "Reg1", "reg1@foobar.com")

        # go to email sender and setup the form and submit it
        self.browser.open(self.portal_url + "/test-event/emailsenderform")
        self.browser.getControl(name='emailtype').value = ['confirmation']
        self.browser.getControl(name='certreq').value = 'on'
        self.browser.getControl(
                name='emailfromaddress').value = 'no-reply@foo.bar'
        self.browser.getControl(
                name='emailtoaddresses').value = '"Reg1" <reg1@foobar.com>'
        self.browser.getControl(name='submit').click()

        # check to see if all is well with the sent emails
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages) > 0, True)
        msg = message_from_string(mailhost.messages[-1])

        self.assertEqual(msg['from'], 'no-reply@foo.bar')
        self.assertEqual(msg['to'], '"Reg1" <reg1@foobar.com>')
        foundcert = False
        for payload in msg.get_payload():
            if 'attachment; filename="certificate.pdf"' in payload.values():
                foundcert = True
                break

        self.assertEqual(foundcert, True)

    def test_create_lodging_report(self):
        pass


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
