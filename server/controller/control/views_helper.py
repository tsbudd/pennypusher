import uuid

from rest_framework import status
from rest_framework.response import Response
from controller.serializers import *


def generate_key():
    while True:
        key = uuid.uuid4().hex[:8].upper()
        if not Pusher.objects.filter(key=key).exists():
            return key


def custom_response(error_description, error_status):
    error_data = {'description': error_description}
    return Response(data=error_data, status=error_status)


def pusher_exists(pusher_name):
    return Pusher.objects.filter(key=pusher_name).exists()


def user_exists(username):
    return User.objects.filter(username=username).exists()


def user_has_access(user, pusher):
    return PusherAccess.objects.filter(user=user, pusher=pusher).exists()


def entity_type_exists(e_type):
    allowed_types = ['income', 'expense', 'paycheck', 'profit', 'bill', 'subscription', 'for_sale',
                     'desired_purchase', 'net_worth', 'budget', 'fund', 'account', 'budget_value',
                     'fund_value', 'account_value']
    return e_type in allowed_types


def handle_valid_request(pusher_key, e_type, user):
    if not pusher_exists(pusher_key):
        return custom_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)
    pusher = Pusher.objects.get(key=pusher_key)
    if not user_has_access(user, pusher):
        return custom_response("The user " + user + " does not have access to the pusher.",
                               status.HTTP_401_UNAUTHORIZED)
    if not entity_type_exists(e_type):
        return custom_response("The type " + e_type + " is not allowed.", status.HTTP_400_BAD_REQUEST)

    return pusher


def handle_ingestion(e_type, pusher, request_data):
    if e_type == 'bill':
        return handle_bill_ingestion(pusher, request_data)
    if 'budget' in request_data or 'fund' in request_data or 'account' in request_data:
        request_data = check_encapsulation_validity(request_data, pusher)
        if isinstance(request_data, Response):
            return request_data

    if e_type in ['subscription', 'for_sale', 'desired_purchase']:
        item = request_data['item']
        if elective_exists(e_type, pusher, item):
            return custom_response("The " + e_type + " [" + item + "] already exists.",
                                   status.HTTP_400_BAD_REQUEST)

    serializer = get_serializer(e_type, request_data, False)
    if serializer.is_valid():
        serializer.save()
        return Response(data=serializer.data)
    else:
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def handle_modification(e_type, pusher, request_data):
    if e_type == 'bill':
        return handle_bill_modification(pusher, request_data)
    if 'budget' in request_data or 'fund' in request_data or 'account' in request_data:
        request_data = check_encapsulation_validity(request_data, pusher)
        if isinstance(request_data, Response):
            return request_data

    # get original encapsulation/elective
    if e_type in ['subscription', 'for_sale', 'desired_purchase']:
        item = request_data['item']
        if not elective_exists(e_type, pusher, item):
            return custom_response("The " + e_type + " [" + item + "] does not exist.",
                                   status.HTTP_400_BAD_REQUEST)
        original = get_elective(e_type, pusher, item)
    else:
        name = request_data['name']
        original = get_encapsulation(e_type, name, pusher)

    serializer = get_serializer(e_type, request_data, False)
    if serializer.is_valid():
        original.delete()
        serializer.save()
        return Response(data=serializer.data)
    else:
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_serializer(e_type, data, many):
    match e_type:
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
        case 'net_worth':
            return ExpNetWorthSerializer(data=data, many=many)
        case 'bill':
            return BillSerializer(data=data, many=many)
        case 'subscription':
            return SubscriptionSerializer(data=data, many=many)
        case 'for_sale':
            return TradeSerializer(data=data, many=many)
        case 'desired_purchase':
            return TradeSerializer(data=data, many=many)


# ------------------------------------------ ENTITY ------------------------------------------
def entity_exists(e_type, pusher, timestamp):
    match e_type:
        case 'income':
            return Income.objects.filter(pusher=pusher, timestamp=timestamp).exists()
        case 'expense':
            return Expense.objects.filter(pusher=pusher, timestamp=timestamp).exists()
        case 'paycheck':
            return Paycheck.objects.filter(pusher=pusher, timestamp=timestamp).exists()
        case 'net_worth':
            return ExpNetWorth.objects.filter(pusher=pusher, timestamp=timestamp).exists()
        case 'bill':
            return Bills.objects.filter(pusher=pusher, timestamp=timestamp).exists()


def get_entity(e_type, pusher, timestamp):
    match e_type:
        case 'income':
            return Income.objects.get(pusher=pusher, timestamp=timestamp)
        case 'expense':
            return Expense.objects.get(pusher=pusher, timestamp=timestamp)
        case 'paycheck':
            return Paycheck.objects.get(pusher=pusher, timestamp=timestamp)
        case 'net_worth':
            return ExpNetWorth.objects.get(pusher=pusher, timestamp=timestamp)
        case 'bill':
            return Bills.objects.get(pusher=pusher, timestamp=timestamp)


def get_entity_list(e_type, pusher):
    match e_type:
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
        case 'subscription':
            return Subscription.objects.filter(pusher=pusher)
        case 'for_sale':
            return Trade.objects.filter(pusher=pusher, type='for_sale')
        case 'desired_purchase':
            return Trade.objects.filter(pusher=pusher, type='desired_purchase')
        case 'bill':
            return Bills.objects.filter(pusher=pusher)


# ------------------------------------------ ELECTIVE ------------------------------------------
def elective_exists(e_type, pusher, item, due_date=None):
    match e_type:
        case 'subscription':
            return Subscription.objects.filter(pusher=pusher, item=item).exists()
        case 'bill':
            return Bills.objects.filter(pusher=pusher, item=item, due_date=due_date).exists()
        case 'for_sale':
            return Trade.objects.filter(pusher=pusher, item=item, type='for_sale').exists()
        case 'desired_purchase':
            return Trade.objects.filter(pusher=pusher, item=item, type='desired_purchase').exists()


def get_elective(e_type, pusher, item, due_date=None):
    match e_type:
        case 'subscription':
            return Subscription.objects.get(pusher=pusher, item=item)
        case 'bill':
            return Bills.objects.get(pusher=pusher, item=item, due_date=due_date)
        case 'for_sale':
            return Trade.objects.get(pusher=pusher, item=item, type='for_sale')
        case 'desired_purchase':
            return Trade.objects.get(pusher=pusher, item=item, type='desired_purchase')


# ------------------------------------------ ENCAPSULATION ------------------------------------------
def encapsulation_exists(e_type, name, pusher):
    if e_type == 'budget':
        return Budget.objects.filter(pusher=pusher, name=name).exists()
    elif e_type == 'fund':
        return Fund.objects.filter(pusher=pusher, name=name).exists()
    elif e_type == 'account':
        return Account.objects.filter(pusher=pusher, name=name).exists()


def get_encapsulation(e_type, e_name, pusher):
    match e_type:
        case 'budget':
            return Budget.objects.get(name=e_name, pusher=pusher)
        case 'fund':
            return Fund.objects.get(name=e_name, pusher=pusher)
        case 'account':
            return Account.objects.get(name=e_name, pusher=pusher)


def get_encapsulation_list(e_type, pusher):
    match e_type:
        case 'budget':
            return BudgetValue.objects.filter(pusher=pusher)
        case 'fund':
            return FundValue.objects.filter(pusher=pusher)
        case 'account':
            return AccountValue.objects.filter(pusher=pusher)


def check_encapsulation_validity(data, pusher):
    if 'budget' in data:
        if not encapsulation_exists('budget', data['budget'], pusher):
            return custom_response("The budget [" + data['budget'] + "] does not exist.",
                                   status.HTTP_400_BAD_REQUEST)
        temp = Budget.objects.get(name=data['budget'], pusher=pusher)
        data.update({'budget': temp.id, 'fund': None})
        return data
    elif 'fund' in data:
        if not encapsulation_exists('fund', data['fund'], pusher):
            return custom_response("The fund [" + data['fund'] + "] does not exist.",
                                   status.HTTP_400_BAD_REQUEST)
        temp = Fund.objects.get(name=data['fund'], pusher=pusher)
        data.update({'fund': temp.id, 'budget': None})
        return data
    elif 'account' in data:
        if not encapsulation_exists('account', data['account'], pusher):
            return custom_response("The account [" + data['account'] + "] does not exist.",
                                   status.HTTP_400_BAD_REQUEST)
        temp = Account.objects.get(name=data['account'], pusher=pusher)
        data.update({'account': temp.id})
        return data


# -------------------------------------- ENCAPSULATION VALUE --------------------------------------
def encapsulation_value_exists(e_type, e_id, timestamp):
    if e_type == 'budget':
        return BudgetValue.objects.filter(budget=e_id, timestamp=timestamp).exists()
    elif e_type == 'fund':
        return FundValue.objects.filter(fund=e_id, timestamp=timestamp).exists()
    elif e_type == 'account':
        return AccountValue.objects.filter(account=e_id, timestamp=timestamp).exists()


def get_encapsulation_value(e_type, e_id, timestamp):
    match e_type:
        case 'budget':
            return BudgetValue.objects.get(budget=e_id, timestamp=timestamp)
        case 'fund':
            return FundValue.objects.get(fund=e_id, timestamp=timestamp)
        case 'account':
            return AccountValue.objects.get(account=e_id, timestamp=timestamp)


def get_encapsulation_value_list(e_type, e_id):
    match e_type:
        case 'budget':
            return BudgetValue.objects.filter(budget=e_id)
        case 'fund':
            return FundValue.objects.filter(fund=e_id)
        case 'account':
            return AccountValue.objects.filter(account=e_id)


# -------------------------------------- BILL Handling --------------------------------------
def handle_bill_ingestion(pusher, request_data):
    # check encapsulation validity
    request_data = check_encapsulation_validity(request_data, pusher)
    if isinstance(request_data, Response):
        return request_data

    # check if bill exists
    item = request_data['item']
    due_date = request_data['due_date']
    if elective_exists('bill', pusher, item, due_date):
        return custom_response("The " + item + " bill due at [" + due_date + "] already exists.",
                               status.HTTP_400_BAD_REQUEST)

    serializer = get_serializer('bill', request_data, False)
    if serializer.is_valid():
        serializer.save()
        return Response(data=serializer.data)
    else:
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def handle_bill_modification(pusher, request_data):
    # checking budget or fund validity
    request_data = check_encapsulation_validity(request_data, pusher)
    if isinstance(request_data, Response):
        return request_data

    # getting original bill
    item = request_data['item']
    due_date = request_data['due_date']
    if not elective_exists('bill', pusher, item, due_date):
        return custom_response("The" + item + " bill due at [" + due_date + "] does not exist.",
                               status.HTTP_400_BAD_REQUEST)
    original = get_elective('bill', pusher, item, due_date)

    serializer = get_serializer('bill', request_data, False)
    if serializer.is_valid():
        original.delete()
        serializer.save()
        return Response(data=serializer.data)
    else:
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
