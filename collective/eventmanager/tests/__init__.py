from Products.CMFCore.utils import getToolByName
from collective.eventmanager.testing import \
    EventManager_INTEGRATION_TESTING
from plone.app.testing import setRoles
import unittest
from plone.app.testing import TEST_USER_ID
from collective.eventmanager.interfaces import ILayer
from zope.interface import alsoProvides


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
        self.workflowTool = getToolByName(self.portal, "portal_workflow")

    def tearDown(self):
        super(PublicEventTest, self).tearDown()

    def doWorkflowTest(self, private_event, private_registration, waiting_list,
                       max_registration, first_state, second_state):
        # setup event values
        self.emevent.privateEvent = private_event
        self.emevent.privateRegistration = private_registration
        self.emevent.enableWaitingList = waiting_list
        self.emevent.maxRegistrations = max_registration

        # first registration
        resultingregid = self.emevent.registrations.invokeFactory(
                        'collective.eventmanager.Registration',
                        'Test Registration 1', email=TEST_USER_ID)
        resultingreg1 = self.emevent.registrations[resultingregid]
        self.assertTrue(len(self.emevent.registrations.objectIds()) >= 1)
        status = self.workflowTool.getStatusOf(
            "collective.eventmanager.Registration_workflow", resultingreg1)
        self.assertEqual(status['review_state'], first_state)

        resultingregid = self.emevent.registrations.invokeFactory(
                        'collective.eventmanager.Registration',
                        'Test Registration 2', email='test@test.com')
        resultingreg2 = self.emevent.registrations[resultingregid]
        self.assertTrue(len(self.emevent.registrations.objectIds()) >= 2)
        status = self.workflowTool.getStatusOf(
            "collective.eventmanager.Registration_workflow", resultingreg2)
        self.assertEqual(status['review_state'], second_state)

        return (resultingreg1, resultingreg2)
