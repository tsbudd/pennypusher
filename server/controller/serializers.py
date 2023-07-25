from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

UserModel = get_user_model()


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


def get_primaryUser(obj):
    # 'obj.primaryUser' is the User instance, so you can access its 'username' directly
    return obj.primaryUser.username


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
    def create(self, validated_data):
        fund_value = FundValue.objects.create(
            fund=validated_data['fund'],
            value=validated_data['value'],
        )
        fund_value.save()
        return fund_value

    class Meta:
        model = FundValue
        fields = ['fund', 'value', 'timestamp']


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
        fields = ['pusher', 'name', 'acct_number', 'rout_number', 'pusher_key', 'pusher_name']


class AccountValueSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        acct_value = AccountValue.objects.create(
            account=validated_data['account'],
            value=validated_data['value'],
        )
        acct_value.save()
        return acct_value

    class Meta:
        model = AccountValue
        fields = ['account', 'value', 'timestamp']


class PaycheckSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        income = Income.objects.create(
            user=validated_data['user'],
            pusher=validated_data['pusher'],
            item=validated_data['company_name'] + " paycheck",
            amount=validated_data['net_amt'],
            source=validated_data['company_name'],
            category="Paychecks",
        )
        income.save()

        paycheck = Paycheck.objects.create(
            user=validated_data['user'],
            pusher=validated_data['pusher'],
            income=income,
            company_name=validated_data['company_name'],
            hours=validated_data['hours'],
            start_date=validated_data['start_date'],
            end_date=validated_data['end_date'],
            pay_date=validated_data['pay_date'],
            gross_amt=validated_data['gross_amt'],
            pre_tax_deduc=validated_data['pre_tax_deduc'],
            post_tax_deduc=validated_data['post_tax_deduc'],
            federal_with=validated_data['federal_with'],
            state_tax=validated_data['state_tax'],
            city_tax=validated_data['city_tax'],
            medicare=validated_data['medicare'],
            oasdi=validated_data['oasdi'],
            net_amt=validated_data['net_amt'],
        )
        paycheck.save()
        return paycheck

    class Meta:
        model = Paycheck
        fields = ['user', 'pusher', 'company_name', 'hours', 'start_date',
                  'end_date', 'pay_date', 'gross_amt', 'pre_tax_deduc', 'post_tax_deduc',
                  'federal_with', 'state_tax', 'city_tax', 'medicare', 'oasdi', 'net_amt']


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
        expense.save()

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
