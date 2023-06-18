from django.test import TestCase
from server.controller.models import *


# Create your tests here.
class AccountEnvTestCase(TestCase):

    def setup(self):
        self.user = User.objects.create(email="JohnDoe@google.com", password="test",
                                        name_first="John", name_last="Doe",
                                        phone="123-456-7890")
        self.pusher = Pusher.objects.create(primaryUser=self.user, primaryEmail=self.user.email,
                                            secondaryEmail=None, name="Personal Budget")
        self.access = PusherAccess.objects.create(user=self.user, pusher=self.pusher)
        self.budget = Budget.objects.create(pusher=self.pusher, name="Rent", alloc_amt=875.00,
                                            priority=2, pay_period="Monthly", pay_start=None,
                                            category="Housing")
        self.fund = Fund.objects.create(pusher=self.pusher, name="College", goal_amt=12000.00,
                                        priority=2, category="School")
        self.income = Income.objects.create(user=self.user, pusher=self.pusher, item="Textbook",
                                            amount=149.99, source="Chegg", category="School")

    def test_newIncome(self):
        self.assertEqual(self.user, self.income.user)
        self.assertEqual(self.pusher, self.income.pusher)
        # todo test Income

    def test_newExpense(self):
        pass  # todo test Expense
