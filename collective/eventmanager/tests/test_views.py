import unittest2 as unittest
import transaction
from collective.eventmanager.tests import BaseTest
from collective.eventmanager.testing import browserLogin
from plone.testing.z2 import Browser
from Acquisition import aq_base
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost
from zope.component import getSiteManager
from email import message_from_string


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

    def registerNewUser(self, event, name, email):
        self.browser.open(event.absolute_url() + \
            '/registrations/++add++collective.eventmanager.Registration')
        self.browser.getControl(name="form.widgets.title").value = name
        self.browser.getControl(name="form.widgets.email").value = email
        self.browser.getControl('Register').click()

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
        pass

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
        event = self.portal['test-event']
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
        self.browser.getControl('Save').click()
        event = self.portal['test-event']
        self.registerNewUser(event, 'test1', 'test1@foobar.com')
        self.registerNewUser(event, 'test2', 'test2@foobar.com')
        self.browser.open(event.absolute_url())
        assert "Registration is closed" in self.browser.contents

    def test_registration_is_closed_on_dates_closed(self):
        pass

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
        event = self.portal['test-event']
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
            name="form.widgets.thankYouIncludeConfirmation:list").checked = True
        self.browser.getControl('Save').click()
        event = self.portal['test-event']

        # add registration
        self.registerNewUser(event, "Test Registration 1", "test1@foobar.com")

        # check captured messages in the mailhost to verify an email with
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages), 1)
        msg = message_from_string(mailhost.message[0])

        self.assertEqual(msg['To'], 'test1@foobar.com')
        self.assertEqual(
            msg['Subject'],
            self.portal['test-event'].thankYouEMailSubject)
        #self.assertIn(confirmationURL,
        #              self.portal_url + '/test-event/')

        # XXX a confirmation message and link are present
        # TODO: add confirmation message and link to registration email

    def test_registrants_can_cancel(self):
        pass

    def test_waiting_list(self):
        pass

    def test_require_payment(self):
        pass

    def test_past_events_automatically_removed_from_calendar(self):
        pass

    def test_registration_info_can_be_managed_by_admins(self):
        pass

    def test_post_training_data(self):
        pass

    def test_send_training_emails(self):
        pass

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
        pass

    def test_set_event_dates(self):
        pass

    def test_modify_email_templates(self):
        pass

    def test_add_registrations_manually(self):
        pass

    def test_private_event_and_send_invitations_via_email(self):
        pass

    def test_ability_to_search_events(self):
        pass

    def test_checkin_roster(self):
        pass

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
        event = self.portal['test-event']

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
        event = self.portal['test-event']

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
