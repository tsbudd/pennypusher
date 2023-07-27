from django.db import models
from django.contrib.auth.models import User


# ----------------------------------------- PUSHER -----------------------------------------
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


# ----------------------------------------- ENCAPSULATION -----------------------------------------
class CommonEncapsulation(models.Model):
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    name = models.CharField(max_length=15)
    priority = models.IntegerField(default=2, null=True, blank=True)
    category = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        abstract = True


class Budget(CommonEncapsulation, models.Model):
    alloc_amt = models.DecimalField(max_digits=8, decimal_places=2)
    pay_period = models.CharField(max_length=15, default="Monthly")
    pay_start = models.DateField()

    def __str__(self):
        return "BUDGET: %s -> %s -> USER: %s" % (self.name, self.pusher,
                                                 self.pusher.primaryUser.email)


class Fund(CommonEncapsulation, models.Model):
    goal_amt = models.DecimalField(max_digits=11, decimal_places=2)

    def __str__(self):
        return "FUND: %s -> PUSHER: %s -> USER: %s" % (self.name, self.pusher.name, self.pusher.primaryUser.email)


class Account(CommonEncapsulation, models.Model):
    acct_number = models.CharField(max_length=15, null=True, blank=True)
    rout_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return "%d ACCOUNT: %s -> PUSHER: %s -> USER: %s" % \
            (self.id, self.name, self.pusher.name, self.pusher.primaryUser.username)


# ----------------------------------------- ENCAPSULATION VALUE -----------------------------------------
class CommonEncapsulationValue(models.Model):
    value = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class BudgetValue(CommonEncapsulationValue, models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE)

    def __str__(self):
        return "%d VALUE: %.2f -> BUDGET: %s -> %s -> USER: %s" % (self.id, float(self.value), self.budget.name,
                                                                   self.budget.pusher,
                                                                   self.budget.pusher.primaryUser.email)


class FundValue(CommonEncapsulationValue, models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

    def __str__(self):
        return "%d VALUE: %.2f -> FUND: %s -> PUSHER: %s -> USER: %s" % (self.id, float(self.value), self.fund.name,
                                                                         self.fund.pusher.name,
                                                                         self.fund.pusher.primaryUser.email)


class AccountValue(CommonEncapsulationValue, models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    def __str__(self):
        return "%d VALUE: $%.2f -> ACCOUNT: %s -> PUSHER: %s -> USER: %s" % \
            (self.id, float(self.value), self.account.name, self.account.pusher.name,
             self.account.pusher.primaryUser.username)


# ----------------------------------------- ENTITY -----------------------------------------
class CommonEntity(models.Model):
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    item = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        abstract = True


class CommonIncome(CommonEntity, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Income(CommonIncome, models.Model):
    category = models.CharField(max_length=30)
    pass

    def __str__(self):
        return "INCOME: %s -> PUSHER: %s -> USER: %s" % (self.item, self.pusher.name, self.user.email)


class CommonExpense(CommonEntity, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fund = models.ForeignKey(Fund, on_delete=models.SET_NULL, null=True, blank=True)
    budget = models.ForeignKey(Budget, on_delete=models.SET_NULL, null=True, blank=True)
    party = models.CharField(max_length=20)
    category = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "EXPENSE: %s -> PUSHER: %s -> USER: %s" % (self.item, self.pusher.name, self.user.email)


class Expense(CommonExpense, models.Model):
    pass

    def __str__(self):
        return "EXPENSE: %s -> PUSHER: %s -> USER: %s" % (self.item, self.pusher.name, self.user.email)


class Paycheck(CommonIncome, models.Model):
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    gross_amt = models.DecimalField(max_digits=7, decimal_places=2)
    pre_tax_deduc = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    post_tax_deduc = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    federal_with = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    state_tax = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    city_tax = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    medicare = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    oasdi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return "%d PAYCHECK: $%.2f -> COMPANY: %s -> PUSHER: %s -> USER: %s" % \
            (self.id, float(self.amount), self.source, self.pusher.name, self.user.email)


class ExpNetWorth(models.Model):
    pusher = models.ForeignKey(Pusher, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%d NET WORTH: $%.2f -> PUSHER: %s -> USER: %s" % \
            (self.id, float(self.amount), self.pusher.name, self.pusher.primaryUser.username)


class Bills(CommonExpense, models.Model):
    status = models.CharField(max_length=20)
    due_date = models.DateField()

    def __str__(self):
        return "%d BILL: $%.2f -> PUSHER: %s" % \
            (self.id, float(self.amount), self.pusher.name)


class Subscription(CommonEntity, models.Model):
    pay_period = models.CharField(max_length=20)
    start_date = models.DateField()
    status = models.CharField(max_length=20)

    def __str__(self):
        return "%d SUBSCRIPTION: $%.2f -> PUSHER: %s" % \
            (self.id, float(self.amount), self.pusher.name)


class Trade(CommonEntity, models.Model):
    status = models.CharField(max_length=20)
    type = models.CharField(max_length=20)

    def __str__(self):
        return "%d TRADE: $%.2f -> PUSHER: %s" % \
            (self.id, float(self.amount), self.pusher.name)
