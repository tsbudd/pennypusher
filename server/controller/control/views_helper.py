from rest_framework.response import Response
from server.controller.serializers import *


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
    allowed_types = ['income', 'expense', 'paycheck', 'profit', 'bills', 'subscription', 'for_sale']
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
        # case 'bills':
        #     return BillSerializer
        # case 'subscription':
        #     return SubscriptionSerializer
        # case 'for_sale':
        #     return ForSaleSerializer


def get_entity_list(entity_type, pusher):
    match entity_type:
        case 'income':
            return Income.objects.get(pusher=pusher)
        case 'expense':
            return Expense.objects.get(pusher=pusher)
        case 'paycheck':
            return Paycheck.objects.get(pusher=pusher)


def get_entity(entity_type, entity_id):
    match entity_type:
        case 'income':
            return Income.objects.get(id=entity_id)
        case 'expense':
            return Expense.objects.get(id=entity_id)
        case 'paycheck':
            return Paycheck.objects.get(id=entity_id)


def encapsulation_exists(entity_type, entity_name, pusher):
    if entity_type == 'budget':
        return Budget.objects.filter(pusher=pusher, name=entity_name).exists()
    if entity_type == 'fund':
        return Fund.objects.filter(pusher=pusher, name=entity_name).exists()
    if entity_type == 'account':
        return Account.objects.filter(pusher=pusher, name=entity_name).exists()
