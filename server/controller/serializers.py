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
    net_value = Decimal(0.0)
    all_accounts = list(Account.objects.filter(pusher=pusher))
    for a in all_accounts:
        cur_value = a.cur_value or Decimal('0.0')
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

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        write_only_fields = ['password', ]


class PusherSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        pusher = Pusher.objects.create(
            primaryUser=validated_data['primaryUser'],
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
        return obj.primaryUser_id

    def get_username(self, obj):
        return obj.primaryUser.username

    class Meta:
        model = Pusher
        fields = ['name', 'key', 'primaryUser', 'username']  # Remove 'primaryUser' from 'fields'
        write_only_fields = ['primaryUser']


class PusherAccessSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)
    pusher_name = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        pusher_access = PusherAccess.objects.create(
            user=validated_data['user'],
            pusher=validated_data['pusher'],
        )
        pusher_access.save()
        return pusher_access

    def get_pusher_name(self, obj):
        return obj.pusher.name

    def get_username(self, obj):
        return obj.user.username

    class Meta:
        model = PusherAccess
        fields = ['user', 'pusher', 'access_time', 'username', 'pusher_name']
        write_only_fields = ['user', 'pusher']


class BudgetSerializer(serializers.ModelSerializer):
    pusher_name = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        budget = Budget.objects.create(
            pusher=validated_data['pusher'],
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
        fields = ['name', 'alloc_amt', 'priority', 'pay_period', 'pay_start',
                  'category', 'pusher', 'pusher_name', 'pusher_key']


class FundSerializer(serializers.ModelSerializer):
    pusher_name = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        fund = Fund.objects.create(
            pusher=validated_data['pusher'],
            name=validated_data['name'],
            goal_amt=validated_data['goal_amt'],
            priority=validated_data['priority'],
            category=validated_data['category'],
        )
        fund.save()
        return fund

    def get_pusher_name(self, obj):
        return obj.pusher.name

    def get_pusher_key(self, obj):
        return obj.pusher.key

    class Meta:
        model = Fund
        fields = ['name', 'goal_amt', 'priority', 'category', 'pusher', 'pusher_key', 'pusher_name']


class BudgetValueSerializer(serializers.ModelSerializer):
    budget_name = serializers.SerializerMethodField(read_only=True)
    pusher_name = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        budget_value = BudgetValue.objects.create(
            budget=validated_data['budget'],
            value=validated_data['value'],
        )
        budget_value.save()
        return budget_value

    def get_pusher_name(self, obj):
        return obj.budget.pusher.name

    def get_pusher_key(self, obj):
        return obj.budget.pusher.key

    def get_budget_name(self, obj):
        return obj.budget.name

    class Meta:
        model = BudgetValue
        fields = ['budget', 'value', 'timestamp', 'budget_name', 'pusher_key', 'pusher_name']


class FundValueSerializer(serializers.ModelSerializer):
    fund_name = serializers.SerializerMethodField(read_only=True)
    pusher_name = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        fund_value = FundValue.objects.create(
            fund=validated_data['fund'],
            value=validated_data['value'],
        )
        fund_value.save()
        return fund_value

    def get_pusher_name(self, obj):
        return obj.fund.pusher.name

    def get_pusher_key(self, obj):
        return obj.fund.pusher.key

    def get_fund_name(self, obj):
        return obj.fund.name

    class Meta:
        model = FundValue
        fields = ['fund', 'value', 'timestamp', 'fund_name', 'pusher_key', 'pusher_name']


class AccountSerializer(serializers.ModelSerializer):
    pusher_name = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        account = Account.objects.create(
            pusher=validated_data['pusher'],
            name=validated_data['name'],
            acct_number=validated_data['acct_number'],
            rout_number=validated_data['rout_number']
        )
        account.save()
        return account

    def get_pusher_name(self, obj):
        return obj.pusher.name

    def get_pusher_key(self, obj):
        return obj.pusher.key

    class Meta:
        model = Account
        fields = ['pusher', 'name', 'acct_number', 'rout_number', 'pusher_key', 'pusher_name', 'cur_value']


class AccountValueSerializer(serializers.ModelSerializer):
    account_name = serializers.SerializerMethodField(read_only=True)
    pusher_name = serializers.SerializerMethodField(read_only=True)
    pusher_key = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        acct_value = AccountValue.objects.create(
            account=validated_data['account'],
            value=validated_data['value'],
        )

        # handle account update
        handle_net_worth_update(acct_value)

        return acct_value

    def get_pusher_name(self, obj):
        return obj.account.pusher.name

    def get_pusher_key(self, obj):
        return obj.account.pusher.key

    def get_account_name(self, obj):
        return obj.account.name

    class Meta:
        model = AccountValue
        fields = ['account', 'value', 'timestamp', 'account_name', 'pusher_key', 'pusher_name']


class PaycheckSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        paycheck = Paycheck.objects.create(
            item=validated_data['item'],
            user=validated_data['user'],
            pusher=validated_data['pusher'],
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

    class Meta:
        model = Paycheck
        fields = ['user', 'pusher', 'source', 'hours', 'start_date',
                  'end_date', 'timestamp', 'gross_amt', 'pre_tax_deduc', 'post_tax_deduc',
                  'federal_with', 'state_tax', 'city_tax', 'medicare', 'oasdi', 'amount', 'item']


class IncomeSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        income = Income.objects.create(
            user=validated_data['user'],
            pusher=validated_data['pusher'],
            item=validated_data['item'],
            amount=validated_data['amount'],
            source=validated_data['source'],
            category=validated_data['category'],
        )
        income.save()

        return income

    class Meta:
        model = Income
        fields = ['user', 'item', 'amount', 'source', 'category', 'timestamp', 'pusher']


class ExpenseSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        expense = Expense.objects.create(
            user=validated_data['user'],
            pusher=validated_data['pusher'],
            item=validated_data['item'],
            amount=validated_data['amount'],
            party=validated_data['party'],
            fund=validated_data['fund'],
            budget=validated_data['budget'],
            category=validated_data['category'],
        )

        return expense

    class Meta:
        model = Expense
        fields = ['user', 'item', 'amount', 'party', 'fund', 'budget',
                  'category', 'timestamp', 'pusher']


class ExpNetWorthSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        net_worth = ExpNetWorth.objects.create(
            pusher=validated_data['pusher'],
            amount=validated_data['amount'],
        )
        net_worth.save()
        return net_worth

    class Meta:
        model = ExpNetWorth
        fields = ['pusher', 'amount', 'timestamp']


class BillSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        bill = Bills.objects.create(
            user=validated_data['user'],
            pusher=validated_data['pusher'],
            item=validated_data['item'],
            amount=validated_data['amount'],
            party=validated_data['party'],
            fund=validated_data['fund'],
            budget=validated_data['budget'],
            category='Bills',
            status=validated_data['status'],
            due_date=validated_data['due_date']
        )

        return bill

    class Meta:
        model = Bills
        fields = ['pusher', 'user', 'item', 'amount', 'party', 'fund',
                  'budget', 'status', 'due_date', 'timestamp']


class SubscriptionSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        subscription = Subscription.objects.create(
            pusher=validated_data['pusher'],
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
    def create(self, validated_data):
        trade = Trade.objects.create(
            pusher=validated_data['pusher'],
            item=validated_data['item'],
            amount=validated_data['amount'],
            status=validated_data['status'],
            type=validated_data['type']
        )
        return trade

    class Meta:
        model = Trade
        fields = ['pusher', 'item', 'amount', 'status', 'type']
