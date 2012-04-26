import unittest2 as unittest
from collective.eventmanager.tests import BaseTest


class TestTypes(BaseTest):

    def test_create_event(self):
        self.portal.invokeFactory('collective.eventmanager.EMEvent',
                'Test Event')

    def test_create_event_fails_inside_event(self):
        self.portal.invokeFactory('collective.eventmanager.EMEvent',
                'testem')
        em = self.portal.testem
        self.assertRaises(ValueError, em.invokeFactory,
            'collective.eventmanager.EMEvent', 'testem2')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
