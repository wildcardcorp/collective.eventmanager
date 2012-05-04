import unittest2 as unittest
from collective.eventmanager.tests import BaseTest


class TestRegistrationWorkflow(BaseTest):
    def test_pubevent_pubreg_nowait_nomax_registration(self):
        self.emevent.privateEvent = False
        self.emevent.privateRegistration = False
        self.emevent.enableRegistrationList = False
        self.emevent.maxRegistrations = None

        resultingreg = self.emevent.Registrations.invokeFactory(
                        'collective.eventmananger.Registration',
                        'Test Registration 1')

        

    def test_pubevent_pubreg_nowait_max_registration(self):
        pass

    def test_pubevent_pubreg_wait_nomax_registration(self):
        pass

    def test_pubevent_pubreg_wait_max_registration(self):
        pass

    def test_privevent_pubreg_nowait_nomax_registration(self):
        pass

    def test_privevent_pubreg_nowait_max_registration(self):
        pass

    def test_privevent_pubreg_wait_nomax_registration(self):
        pass

    def test_privevent_pubreg_wait_max_registration(self):
        pass

    def test_pubevent_privreg_nowait_nomax_registration(self):
        pass

    def test_pubevent_privreg_nowait_max_registration(self):
        pass

    def test_pubevent_privreg_wait_nomax_registration(self):
        pass

    def test_pubevent_privreg_wait_max_registration(self):
        pass

    def test_privevent_privreg_nowait_nomax_registration(self):
        pass

    def test_privevent_privreg_nowait_max_registration(self):
        pass

    def test_privevent_privreg_wait_nomax_registration(self):
        pass

    def test_privevent_privreg_wait_max_registration(self):
        pass



def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
