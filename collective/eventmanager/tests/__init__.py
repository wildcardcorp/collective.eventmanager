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

        self.emevent = self.portal.invokeFactory(
                    'collective.eventmanager.EMEvent',
                    'Test Event')

    def tearDown(self):
        super(PublicEventTest, self).tearDown()
