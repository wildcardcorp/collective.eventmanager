from collective.eventmanager.testing import \
    EventManager_INTEGRATION_TESTING
from plone.app.testing import setRoles
import unittest
from plone.app.testing import TEST_USER_ID
from collective.eventmanager.interfaces import ILayer
from zope.interface import alsoProvides
from collective.eventmanager.registration import \
    getNumApprovedAndConfirmed


class BaseTest(unittest.TestCase):

    layer = EventManager_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        alsoProvides(self.request, ILayer)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def tearDown(self):
        pass


class PublicEventTest(BaseTest):
    def setUp(self):
        super(PublicEventTest, self).setUp()

        newid = self.portal.invokeFactory(
                    'collective.eventmanager.EMEvent',
                    'Test Event')
        self.emevent = self.portal[newid]

    def tearDown(self):
        super(PublicEventTest, self).tearDown()

    def doWorkflowTest(self, private_event, private_registration, waiting_list,
                       max_registration, first_state, second_state):
        self.emevent.privateEvent = private_event
        self.emevent.privateRegistration = private_registration
        self.emevent.enableRegistrationList = waiting_list
        self.emevent.maxRegistrations = max_registration

        resultingreg = self.emevent.registrations.invokeFactory(
                        'collective.eventmananger.Registration',
                        'Test Registration 1')
        numReg = getNumApprovedAndConfirmed(resultingreg)

        self.assertTrue(numReg >= 1)
        self.assertEqual(resultingreg.review_state, first_state)

        resultingreg = self.emevent.registrations.invokeFactory(
                        'collective.eventmananger.Registration',
                        'Test Registration 2')
        numReg = getNumApprovedAndConfirmed(resultingreg)

        self.assertTrue(numReg >= 2)
        self.assertEqual(resultingreg.review_state, second_state)
