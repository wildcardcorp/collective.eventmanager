import unittest2 as unittest
from collective.eventmanager.tests import PublicEventTest


class TestRegistrationWorkflow(PublicEventTest):
    #### TESTS FOR INITIAL REGISTRATION ####
    def test_pubevent_pubreg_nowait_nomax_registration(self):
        self.doWorkflowTest(False, False, False, None, 'approved', 'approved')

    def test_pubevent_pubreg_nowait_max_registration(self):
        self.doWorkflowTest(False, False, False, 1, 'approved', 'denied')

    def test_pubevent_pubreg_wait_nomax_registration(self):
        self.doWorkflowTest(False, False, True, None, 'approved', 'approved')

    def test_pubevent_pubreg_wait_max_registration(self):
        self.doWorkflowTest(False, False, True, 1, 'approved', 'submitted')

    def test_pubevent_privreg_nowait_nomax_registration(self):
        self.doWorkflowTest(False, True, False, None, 'approved', 'approved')

    def test_pubevent_privreg_nowait_max_registration(self):
        self.doWorkflowTest(False, True, False, 1, 'approved', 'approved')

    def test_pubevent_privreg_wait_nomax_registration(self):
        self.doWorkflowTest(False, True, True, None, 'approved', 'approved')

    def test_pubevent_privreg_wait_max_registration(self):
        self.doWorkflowTest(False, True, True, 1, 'approved', 'approved')

    def test_privevent_pubreg_nowait_nomax_registration(self):
        self.doWorkflowTest(True, False, False, None, 'approved', 'approved')

    def test_privevent_pubreg_nowait_max_registration(self):
        self.doWorkflowTest(True, False, False, 1, 'approved', 'denied')

    def test_privevent_pubreg_wait_nomax_registration(self):
        self.doWorkflowTest(True, False, True, None, 'approved', 'approved')

    def test_privevent_pubreg_wait_max_registration(self):
        self.doWorkflowTest(True, False, True, 1, 'approved', 'submitted')

    def test_privevent_privreg_nowait_nomax_registration(self):
        self.doWorkflowTest(True, True, False, None, 'approved', 'approved')

    def test_privevent_privreg_nowait_max_registration(self):
        self.doWorkflowTest(True, True, False, 1, 'approved', 'approved')

    def test_privevent_privreg_wait_nomax_registration(self):
        self.doWorkflowTest(True, True, True, None, 'approved', 'approved')

    def test_privevent_privreg_wait_max_registration(self):
        self.doWorkflowTest(True, True, True, 1, 'approved', 'approved')

    #### TESTS FOR CONFIRMATION, CANCELLATION, AND DENIAL ####
    def test_modify_denied(self):
        pass

    def test_modify_cancelled(self):
        pass

    def test_cancel_approved(self):
        pass

    def test_cancel_denied(self):
        pass

    def test_cancel_confirmed(self):
        pass

    def test_deny_approved(self):
        pass

    def test_deny_confirmed(self):
        pass

    def test_confirm_approved(self):
        pass


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
