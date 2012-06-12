import unittest2 as unittest
from collective.eventmanager.tests import BaseTest
from collective.eventmanager.testing import browserLogin
from plone.testing.z2 import Browser


class TestViews(BaseTest):

    def setUp(self):
        super(TestViews, self).setUp()
        self.browser = Browser(self.layer['app'])
        self.browser.handleErrors = False
        self.portal_url = self.portal.absolute_url()

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
            name="form.widgets.enableWaitingList:list").checked = True
        self.browser.getControl('Save').click()
        event = self.portal['test-event']
        self.registerNewUser(event, 'test1', 'test1@foobar.com')
        self.registerNewUser(event, 'test2', 'test2@foobar.com')
        self.browser.open(event.absolute_url())
        assert "Registration is closed" not in self.browser.contents

    def test_registrants_receive_confirmation_email_on_signup(self):
        pass

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
        pass

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
        pass

    def test_send_certificate_on_completion(self):
        pass

    def test_create_lodging_report(self):
        pass


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
