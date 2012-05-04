import unittest2 as unittest
from collective.eventmanager.tests import PublicEventTest


class TestRegistrationWorkflow(PublicEventTest):
    def test_pubevent_pubreg_nowait_nomax_registration(self):
        self.doWorkflowTest(False, False, False, None, 'Approved', 'Approved')

    def test_pubevent_pubreg_nowait_max_registration(self):
        self.doWorkflowTest(False, False, False, 1, 'Approved', 'Denied')

    def test_pubevent_pubreg_wait_nomax_registration(self):
        self.doWorkflowTest(False, False, True, None, 'Approved', 'Approved')

    def test_pubevent_pubreg_wait_max_registration(self):
        self.doWorkflowTest(False, False, True, 1, 'Approved', 'Submitted')

    def test_privevent_pubreg_nowait_nomax_registration(self):
        self.doWorkflowTest(True, False, False, None, 'Approved', 'Approved')

    def test_privevent_pubreg_nowait_max_registration(self):
        self.doWorkflowTest(True, False, False, 1, 'Approved', 'Denied')

    def test_privevent_pubreg_wait_nomax_registration(self):
        self.doWorkflowTest(True, False, True, None, 'Approved', 'Approved')

    def test_privevent_pubreg_wait_max_registration(self):
        self.doWorkflowTest(True, False, True, 1, 'Approved', 'Denied')

    def test_pubevent_privreg_nowait_nomax_registration(self):
        self.doWorkflowTest(False, True, False, None, 'Approved', 'Approved')

    def test_pubevent_privreg_nowait_max_registration(self):
        self.doWorkflowTest(False, True, False, 1, 'Approved', 'Denied')

    def test_pubevent_privreg_wait_nomax_registration(self):
        self.doWorkflowTest(False, True, True, None, 'Approved', 'Approved')

    def test_pubevent_privreg_wait_max_registration(self):
        self.doWorkflowTest(False, True, True, 1, 'Approved', 'Submitted')

    def test_privevent_privreg_nowait_nomax_registration(self):
        self.doWorkflowTest(True, True, False, None, 'Approved', 'Approved')

    def test_privevent_privreg_nowait_max_registration(self):
        self.doWorkflowTest(True, True, False, 1, 'Approved', 'Denied')

    def test_privevent_privreg_wait_nomax_registration(self):
        self.doWorkflowTest(True, True, True, None, 'Approved', 'Approved')

    def test_privevent_privreg_wait_max_registration(self):
        self.doWorkflowTest(True, True, True, 1, 'Approved', 'Submitted')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
