from datetime import datetime

from rest_framework import status
from rest_framework.response import Response
from controller.serializers import *


def generate_key():
    while True:
        key = uuid.uuid4().hex[:8].upper()
        if not Pusher.objects.filter(key=key).exists():
            return key


def failure_response(error_description, error_status):
    error_data = {'description': error_description}
    return Response(data=error_data, status=error_status)


def pusher_exists(pusher_name):
    return Pusher.objects.filter(key=pusher_name).exists()


def user_exists(username):
    return User.objects.filter(username=username).exists()


def user_has_access(user, pusher):
    return PusherAccess.objects.filter(user=user, pusher=pusher).exists()


def entity_type_exists(entity_type):
    allowed_types = ['income', 'expense', 'paycheck', 'profit', 'bills', 'subscription', 'for_sale',
                     'budget', 'fund', 'account']
    return entity_type in allowed_types


def encapsulation_type_exists(entity_type):
    allowed_types = ['budget', 'fund', 'account']
    return entity_type in allowed_types


def get_serializer(entity_type, data, many):
    match entity_type:
        case 'income':
            return IncomeSerializer(data=data, many=many)
        case 'expense':
            return ExpenseSerializer(data=data, many=many)
        case 'paycheck':
            return PaycheckSerializer(data=data, many=many)
        case 'budget':
            return BudgetSerializer(data=data, many=many)
        case 'fund':
            return FundSerializer(data=data, many=many)
        case 'account':
            return AccountSerializer(data=data, many=many)
        case 'budget_value':
            return BudgetValueSerializer(data=data, many=many)
        case 'fund_value':
            return FundValueSerializer(data=data, many=many)
        case 'account_value':
            return AccountValueSerializer(data=data, many=many)
        # case 'bills':
        #     return BillSerializer
        # case 'subscription':
        #     return SubscriptionSerializer
        # case 'for_sale':
        #     return ForSaleSerializer


def get_entity_list(entity_type, pusher):
    match entity_type:
        case 'income':
            return Income.objects.filter(pusher=pusher)
        case 'expense':
            return Expense.objects.filter(pusher=pusher)
        case 'paycheck':
            return Paycheck.objects.filter(pusher=pusher)
        case 'budget':
            return Budget.objects.filter(pusher=pusher)
        case 'fund':
            return Fund.objects.filter(pusher=pusher)
        case 'account':
            return Account.objects.filter(pusher=pusher)
        case 'budget_value':
            return BudgetValue.objects.filter(pusher=pusher)
        case 'fund_value':
            return FundValue.objects.filter(pusher=pusher)
        case 'fund_value':
            return AccountValue.objects.filter(pusher=pusher)


def get_encapsulation_value_list(encapsulation_type, encapsulation_id):
    match encapsulation_type:
        case 'budget':
            return BudgetValue.objects.filter(budget=encapsulation_id)
        case 'fund':
            return FundValue.objects.filter(fund=encapsulation_id)
        case 'account':
            return AccountValue.objects.filter(account=encapsulation_id)


def get_encapsulation(encapsulation_type, encapsulation_name):
    match encapsulation_type:
        case 'budget':
            return Budget.objects.get(name=encapsulation_name)
        case 'fund':
            return Fund.objects.get(name=encapsulation_name)
        case 'account':
            return Account.objects.get(name=encapsulation_name)


def get_encapsulation_value(encapsulation_type, encapsulation_id, timestamp):
    match encapsulation_type:
        case 'budget':
            return BudgetValue.objects.get(budget=encapsulation_id, timestamp=timestamp)
        case 'fund':
            return FundValue.objects.get(fund=encapsulation_id, timestamp=timestamp)
        case 'account':
            return AccountValue.objects.get(account=encapsulation_id, timestamp=timestamp)


def entity_exists(entity_type, pusher, timestamp):
    match entity_type:
        case 'income':
            return Income.objects.filter(pusher=pusher, timestamp=timestamp).exists()
        case 'expense':
            return Expense.objects.filter(pusher=pusher, timestamp=timestamp).exists()
        case 'paycheck':
            return Paycheck.objects.filter(pusher=pusher, pay_date=timestamp).exists()


def get_entity(entity_type, pusher, timestamp):
    match entity_type:
        case 'income':
            return Income.objects.get(pusher=pusher, timestamp=timestamp)
        case 'expense':
            return Expense.objects.get(pusher=pusher, timestamp=timestamp)
        case 'paycheck':
            return Paycheck.objects.get(pusher=pusher, pay_date=timestamp)


def encapsulation_exists(entity_type, entity_name, pusher):
    if entity_type == 'budget':
        return Budget.objects.filter(pusher=pusher, name=entity_name).exists()
    elif entity_type == 'fund':
        return Fund.objects.filter(pusher=pusher, name=entity_name).exists()
    elif entity_type == 'account':
        return Account.objects.filter(pusher=pusher, name=entity_name).exists()


def encapsulation_value_exists(encapsulation_type, encapsulation_id, timestamp):
    if encapsulation_type == 'budget':
        return BudgetValue.objects.filter(budget=encapsulation_id, timestamp=timestamp).exists()
    elif encapsulation_type == 'fund':
        return FundValue.objects.filter(fund=encapsulation_id, timestamp=timestamp).exists()
    elif encapsulation_type == 'account':
        return AccountValue.objects.filter(account=encapsulation_id, timestamp=timestamp).exists()


def check_budget_validity(data, pusher):
    if 'budget' in data:
        if not encapsulation_exists('budget', data['budget'], pusher):
            return failure_response("The budget [" + data['budget'] + "] does not exist.",
                                    status.HTTP_400_BAD_REQUEST)
        temp = Budget.objects.get(name=data['budget'], pusher=pusher)
        data.update({'budget': temp.id, 'fund': None})
        return data
    elif 'fund' in data:
        if not encapsulation_exists('fund', data['fund'], pusher):
            return failure_response("The fund [" + data['fund'] + "] does not exist.",
                                    status.HTTP_400_BAD_REQUEST)
        temp = Budget.objects.get(name=data['fund'], pusher=pusher)
        data.update({'fund': temp.id, 'budget': None})
        return data


def handle_paycheck_delete(pusher, entity_timestamp):
    timestamp = datetime.strptime(entity_timestamp, '%Y-%m-%d').date()
    if not entity_exists('paycheck', pusher, timestamp):
        return failure_response("The paycheck at [" + entity_timestamp + "] does not exist.",
                                status.HTTP_400_BAD_REQUEST)
    paycheck = get_entity('paycheck', pusher, timestamp)
    income = paycheck.income

    # delete both paycheck and income
    paycheck.delete()
    income.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

