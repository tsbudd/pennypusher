import uuid
from django.db import models
from django.contrib.auth.models import User


class Pusher(models.Model):
    primaryUser = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    key = models.CharField(max_length=8, unique=True)

    def __str__(self):
        return "PUSHER: %s -> PRIMARY USER: %s" % (self.name, self.primaryUser.username)


class PusherAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE, null=True)
    access_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "USER: %s -> %s -> ACCESS_TIME:%s" % (self.user.email, self.pusher, self.access_time)


class Budget(models.Model):
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    name = models.CharField(max_length=15)
    alloc_amt = models.DecimalField(max_digits=8, decimal_places=2)
    priority = models.IntegerField(default=2)
    pay_period = models.CharField(max_length=15, default="Monthly")
    pay_start = models.DateField()
    category = models.CharField(max_length=15)

    def __str__(self):
        return "BUDGET: %s -> %s -> USER: %s" % (self.name, self.pusher,
                                                 self.pusher.primaryUser.email)


class BudgetValue(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    timestamp = models.DateField(auto_now_add=True)

    def __str__(self):
        return "%d VALUE: %.2f -> BUDGET: %s -> %s -> USER: %s" % (self.id, float(self.value), self.budget.name,
                                                                   self.budget.pusher,
                                                                   self.budget.pusher.primaryUser.email)


class Fund(models.Model):
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    name = models.CharField(max_length=15)
    goal_amt = models.DecimalField(max_digits=11, decimal_places=2)
    priority = models.IntegerField(default=2)
    category = models.CharField(max_length=15)

    def __str__(self):
        return "FUND: %s -> PUSHER: %s -> USER: %s" % (self.name, self.pusher.name, self.pusher.primaryUser.email)


class FundValue(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)
    timestamp = models.DateField(auto_now_add=True)

    def __str__(self):
        return "%d VALUE: %.2f -> FUND: %s -> PUSHER: %s -> USER: %s" % (self.id, float(self.value), self.fund.name,
                                                                         self.fund.pusher.name,
                                                                         self.fund.pusher.primaryUser.email)


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    item = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    source = models.CharField(max_length=20)
    category = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "INCOME: %s -> PUSHER: %s -> USER: %s" % (self.item, self.pusher.name, self.user.email)


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    item = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    party = models.CharField(max_length=20)
    fund = models.ForeignKey(Fund, on_delete=models.SET_NULL, null=True, blank=True)
    budget = models.ForeignKey(Budget, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "EXPENSE: %s -> PUSHER: %s -> USER: %s" % (self.item, self.pusher.name, self.user.email)


class Paycheck(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    income = models.ForeignKey(Income, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=20)
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    pay_date = models.DateField()
    gross_amt = models.DecimalField(max_digits=7, decimal_places=2)
    pre_tax_deduc = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    post_tax_deduc = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    federal_with = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    state_tax = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    city_tax = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    medicare = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    oasdi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    net_amt = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return "%d PAYCHECK: $%.2f -> COMPANY: %s -> PUSHER: %s -> USER: %s" % \
               (self.id, float(self.net_amt), self.company_name, self.pusher.name, self.user.email)


class Profit(models.Model):
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%d PROFIT: $%.2f -> PUSHER: %s -> USER: %s" % \
               (self.id, float(self.amount), self.pusher.name, self.pusher.primaryUser.username)


class Account(models.Model):
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    acct_number = models.CharField(max_length=15, null=True, blank=True)
    rout_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return "%d ACCOUNT: %s -> PUSHER: %s -> USER: %s" % \
               (self.id, self.name, self.pusher.name, self.pusher.primaryUser.username)


class AccountValue(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%d VALUE: $%.2f -> ACCOUNT: %s -> PUSHER: %s -> USER: %s" % \
               (self.id, float(self.value), self.account.name, self.account.pusher.name,
                self.account.pusher.primaryUser.username)


class ExpNetWorth(models.Model):
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%d NET WORTH: $%.2f -> PUSHER: %s -> USER: %s" % \
               (self.id, float(self.amount), self.pusher.name, self.pusher.primaryUser.username)
