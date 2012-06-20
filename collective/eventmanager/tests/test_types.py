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

    def test_creating_event_creates_sub_directories(self):
        self.portal.invokeFactory('collective.eventmanager.EMEvent',
                'testem2')
        event = self.portal.testem2
        self.assertEquals(set(event.objectIds()),
            set(['sessions', 'session-calendar', 'registrations',
                 'travel-accommodations', 'lodging-accommodations',
                 'announcements']))

    def test_folder_creation_restrictions(self):
        self.portal.invokeFactory('collective.eventmanager.EMEvent',
                'testem3')
        event = self.portal.testem3
        event.registrations.invokeFactory(
            'collective.eventmanager.Registration', 'reg',
            title='something', email='test@test.com')
        event.sessions.invokeFactory(
            'collective.eventmanager.Session', 'ses')
        event['travel-accommodations'].invokeFactory(
            'collective.eventmanager.Accommodation', 'tra')
        event['lodging-accommodations'].invokeFactory(
            'collective.eventmanager.Accommodation', 'lod')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
