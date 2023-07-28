import decimal

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

UserModel = get_user_model()


def handle_net_worth_update(acct_value):
    # update account
    account = Account.objects.get(id=acct_value.account.id)
    account.cur_value = acct_value.value
    account.save()

    # get net worth
    pusher = acct_value.account.pusher
    net_value = decimal.Decimal(0.0)
    all_accounts = list(Account.objects.filter(pusher=pusher))
    for a in all_accounts:
        cur_value = a.cur_value or decimal.Decimal('0.0')
        net_value += cur_value

    # add to exp Net worth
    net_worth = ExpNetWorth.objects.create(
        pusher=pusher,
        amount=net_value
    )
    net_worth.save()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = UserModel.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)

        # Only update the password if it's provided
        password = validated_data.get('password', None)
        if password is not None:
            instance.set_password(password)

        instance.save()

        return instance

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        write_only_fields = ['password', ]


class PusherSerializer(serializers.ModelSerializer):
    primaryUser = serializers.SerializerMethodField(read_only=True)
    user = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user_instance = User.objects.get(id=validated_data['user'])

        pusher = Pusher.objects.create(
            primaryUser=user_instance,
            name=validated_data['name'],
            key=validated_data['key'],
        )
        pusher.save()

        user_access = PusherAccess.objects.create(
            user=pusher.primaryUser,
            pusher=pusher
        )
        user_access.save()

        return pusher

    def get_primaryUser(self, obj):
        return obj.primaryUser.username

    class Meta:
        model = Pusher
        fields = ['name', 'primaryUser', 'key', 'user']


class PusherAccessSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)
    user = serializers.CharField(write_only=True)
    pusher = serializers.CharField(write_only=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])
        user_instance = User.objects.get(id=validated_data['user'])

        pusher_access = PusherAccess.objects.create(
            user=user_instance,
            pusher=pusher_instance,
        )
        pusher_access.save()
        return pusher_access

    def get_pusher_key(self, obj):
        return obj.pusher.key

    def get_username(self, obj):
        return obj.user.username

    class Meta:
        model = PusherAccess
        fields = ['user', 'pusher', 'pusher_key', 'username', 'access_time']
        write_only_fields = ['user', 'pusher']


class BudgetSerializer(serializers.ModelSerializer):
    pusher_key = serializers.SerializerMethodField(read_only=True)
    pusher = serializers.CharField(write_only=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])

        budget = Budget.objects.create(
            pusher=pusher_instance,
            name=validated_data['name'],
            alloc_amt=validated_data['alloc_amt'],
            priority=validated_data['priority'],
            pay_period=validated_data['pay_period'],
            pay_start=validated_data['pay_start'],
            category=validated_data['category'],
        )
        budget.save()
        return budget

    def get_pusher_name(self, obj):
        return obj.pusher.name

    def get_pusher_key(self, obj):
        return obj.pusher.key

    class Meta:
        model = Budget
        fields = ['pusher_key', 'name', 'alloc_amt', 'priority', 'pay_period', 'pay_start',
                  'category', 'pusher', ]


class FundSerializer(serializers.ModelSerializer):
    pusher_key = serializers.SerializerMethodField(read_only=True)
    pusher = serializers.CharField(write_only=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])

        fund = Fund.objects.create(
            pusher=pusher_instance,
            name=validated_data['name'],
            goal_amt=validated_data['goal_amt'],
            priority=validated_data['priority'],
            category=validated_data['category'],
        )
        fund.save()
        return fund

    def get_pusher_key(self, obj):
        return obj.pusher.key

    class Meta:
        model = Fund
        fields = ['pusher_key', 'name', 'goal_amt', 'priority', 'category', 'pusher']


class AccountSerializer(serializers.ModelSerializer):
    pusher_key = serializers.SerializerMethodField(read_only=True)
    pusher = serializers.CharField(write_only=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])

        account = Account.objects.create(
            pusher=pusher_instance,
            name=validated_data['name'],
            acct_number=validated_data['acct_number'],
            rout_number=validated_data['rout_number']
        )
        account.save()
        return account

    def get_pusher_key(self, obj):
        return obj.pusher.key

    class Meta:
        model = Account
        fields = ['pusher', 'pusher_key', 'name', 'cur_value', 'acct_number', 'rout_number']


class BudgetValueSerializer(serializers.ModelSerializer):
    budget_name = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)
    budget = serializers.CharField(write_only=True)

    def create(self, validated_data):
        budget_instance = Budget.objects.get(id=validated_data['budget'])

        budget_value = BudgetValue.objects.create(
            budget=budget_instance,
            value=validated_data['value'],
        )
        budget_value.save()
        return budget_value

    def get_budget_name(self, obj):
        return obj.budget.name

    def get_pusher_key(self, obj):
        return obj.budget.pusher.key

    class Meta:
        model = BudgetValue
        fields = ['pusher_key', 'budget', 'budget_name', 'value', 'timestamp']


class FundValueSerializer(serializers.ModelSerializer):
    fund_name = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)
    fund = serializers.CharField(write_only=True)

    def create(self, validated_data):
        fund_instance = Fund.objects.get(id=validated_data['fund'])

        fund_value = FundValue.objects.create(
            fund=fund_instance,
            value=validated_data['value'],
        )
        return fund_value

    def get_pusher_key(self, obj):
        return obj.fund.pusher.key

    def get_fund_name(self, obj):
        return obj.fund.name

    class Meta:
        model = FundValue
        fields = ['fund', 'pusher_key', 'fund_name', 'value', 'timestamp', ]


class AccountValueSerializer(serializers.ModelSerializer):
    account_name = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)
    account = serializers.CharField(write_only=True)

    def create(self, validated_data):
        account_instance = Account.objects.get(id=validated_data['account'])

        acct_value = AccountValue.objects.create(
            account=account_instance,
            value=validated_data['value'],
        )

        # handle account update
        handle_net_worth_update(acct_value)

        return acct_value

    def get_pusher_key(self, obj):
        return obj.account.pusher.key

    def get_account_name(self, obj):
        return obj.account.name

    class Meta:
        model = AccountValue
        fields = ['pusher_key', 'account_name', 'account', 'value', 'timestamp', ]


class ExpNetWorthSerializer(serializers.ModelSerializer):
    pusher = serializers.CharField(write_only=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])

        net_worth = ExpNetWorth.objects.create(
            pusher=pusher_instance,
            amount=validated_data['amount'],
        )
        net_worth.save()
        return net_worth

    class Meta:
        model = ExpNetWorth
        fields = ['pusher', 'timestamp', 'amount']


class IncomeSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)
    pusher = serializers.CharField(write_only=True)
    user = serializers.CharField(write_only=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])
        user_instance = User.objects.get(id=validated_data['user'])

        income = Income.objects.create(
            user=user_instance,
            pusher=pusher_instance,
            item=validated_data['item'],
            amount=validated_data['amount'],
            source=validated_data['source'],
            category=validated_data['category'],
        )
        income.save()

        return income

    def get_username(self, obj):
        return obj.user.username

    class Meta:
        model = Income
        fields = ['user', 'username', 'item', 'amount', 'source', 'category', 'timestamp', 'pusher']


class ExpenseSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)
    budget_name = serializers.SerializerMethodField(read_only=True)
    fund_name = serializers.SerializerMethodField(read_only=True)
    pusher = serializers.CharField(write_only=True)
    user = serializers.CharField(write_only=True)
    fund = serializers.CharField(write_only=True, allow_null=True)
    budget = serializers.CharField(write_only=True, allow_null=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])
        user_instance = User.objects.get(id=validated_data['user'])

        expense = Expense.objects.create(
            user=user_instance,
            pusher=pusher_instance,
            item=validated_data['item'],
            amount=validated_data['amount'],
            party=validated_data['party'],
            category=validated_data['category'],
        )

        if 'budget' in validated_data and validated_data['budget'] is not None:
            budget_instance = Budget.objects.get(id=validated_data['budget'])
            expense.budget = budget_instance

        if 'fund' in validated_data and validated_data['fund'] is not None:
            fund_instance = Fund.objects.get(id=validated_data['fund'])
            expense.fund = fund_instance

        return expense

    def get_username(self, obj):
        return obj.user.username

    def get_budget_name(self, obj):
        if obj.budget is None:
            return None
        return obj.budget.name

    def get_fund_name(self, obj):
        if obj.fund is None:
            return None
        return obj.fund.name

    class Meta:
        model = Expense
        fields = ['user', 'username', 'item', 'amount', 'party', 'fund', 'fund_name',
                  'budget', 'budget_name', 'category', 'timestamp', 'pusher']


class PaycheckSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)
    pusher = serializers.CharField(write_only=True)
    user = serializers.CharField(write_only=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])
        user_instance = User.objects.get(id=validated_data['user'])

        paycheck = Paycheck.objects.create(
            item=validated_data['source'] + ' paycheck',
            user=user_instance,
            pusher=pusher_instance,
            source=validated_data['source'],
            hours=validated_data['hours'],
            start_date=validated_data['start_date'],
            end_date=validated_data['end_date'],
            gross_amt=validated_data['gross_amt'],
            pre_tax_deduc=validated_data['pre_tax_deduc'],
            post_tax_deduc=validated_data['post_tax_deduc'],
            federal_with=validated_data['federal_with'],
            state_tax=validated_data['state_tax'],
            city_tax=validated_data['city_tax'],
            medicare=validated_data['medicare'],
            oasdi=validated_data['oasdi'],
            amount=validated_data['amount']
        )
        return paycheck

    def get_username(self, obj):
        return obj.user.username

    class Meta:
        model = Paycheck
        fields = ['user', 'username', 'pusher', 'source', 'hours', 'start_date',
                  'end_date', 'timestamp', 'gross_amt', 'pre_tax_deduc', 'post_tax_deduc',
                  'federal_with', 'state_tax', 'city_tax', 'medicare', 'oasdi', 'amount']


class BillSerializer(serializers.ModelSerializer):

    username = serializers.SerializerMethodField(read_only=True)
    budget_name = serializers.SerializerMethodField(read_only=True)
    fund_name = serializers.SerializerMethodField(read_only=True)
    pusher = serializers.CharField(write_only=True)
    user = serializers.CharField(write_only=True)
    fund = serializers.CharField(write_only=True, allow_null=True)
    budget = serializers.CharField(write_only=True, allow_null=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])
        user_instance = User.objects.get(id=validated_data['user'])

        bill = Bills.objects.create(
            user=user_instance,
            pusher=pusher_instance,
            item=validated_data['item'],
            amount=validated_data['amount'],
            party=validated_data['party'],
            category='Bills',
            status=validated_data['status'],
            due_date=validated_data['due_date']
        )

        if 'budget' in validated_data and validated_data['budget'] is not None:
            budget_instance = Budget.objects.get(id=validated_data['budget'])
            bill.budget = budget_instance

        if 'fund' in validated_data and validated_data['fund'] is not None:
            fund_instance = Fund.objects.get(id=validated_data['fund'])
            bill.fund = fund_instance

        return bill

    def get_username(self, obj):
        return obj.user.username

    def get_budget_name(self, obj):
        if obj.budget is None:
            return None
        return obj.budget.name

    def get_fund_name(self, obj):
        if obj.fund is None:
            return None
        return obj.fund.name

    class Meta:
        model = Bills
        fields = ['pusher', 'user', 'username', 'item', 'amount', 'party', 'fund',
                  'fund_name', 'budget', 'budget_name', 'status', 'due_date', 'timestamp']


class SubscriptionSerializer(serializers.ModelSerializer):
    pusher = serializers.CharField(write_only=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])

        subscription = Subscription.objects.create(
            pusher=pusher_instance,
            item=validated_data['item'],
            amount=validated_data['amount'],
            pay_period=validated_data['pay_period'],
            start_date=validated_data['start_date'],
            status=validated_data['status']
        )
        return subscription

    class Meta:
        model = Subscription
        fields = ['pusher', 'item', 'amount', 'pay_period', 'start_date', 'status']


class TradeSerializer(serializers.ModelSerializer):
    pusher = serializers.CharField(write_only=True)
    type = serializers.CharField(write_only=True)

    def create(self, validated_data):
        pusher_instance = Pusher.objects.get(id=validated_data['pusher'])

        trade = Trade.objects.create(
            pusher=pusher_instance,
            item=validated_data['item'],
            amount=validated_data['amount'],
            status=validated_data['status'],
            type=validated_data['type']
        )
        return trade

    class Meta:
        model = Trade
        fields = ['pusher', 'item', 'amount', 'status', 'type']
