from django.http import HttpResponse

from .serializers import *
from .models import *
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from ratelimit import limits


def index(request):
    return HttpResponse("PennyPusher Index")


# -------------------------------------------- CONNECTION --------------------------------------------
# @limits(calls=100, period=900)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def connect_stat(request, format=None):
    return Response(status=status.HTTP_200_OK)


# -------------------------------------------- USER --------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([permissions.IsAdminUser])
def user_all(request, format=None):
    data = User.objects.all()
    serializer = UserSerializer(data, many=True)
    return Response(serializer.data)


# @limits(key='ip', rate='100/h')
@api_view(['DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([permissions.IsAdminUser])
def user_delete(request, format=None):
    try:
        user = User.objects.get(username=request.data["user"])
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except User.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_register(request, format=None):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'PUT'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def user_info(request, format=None):
    try:
        user = request.user
    except User.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------- PUSHER ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_all(request, format=None):
    data = Pusher.objects.filter(primaryUser=request.user)
    serializer = PusherSerializer(data=data, many=True)

    if not serializer.is_valid():
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def generate_key():
    while True:
        key = uuid.uuid4().hex[:8].upper()
        if not Pusher.objects.filter(key=key).exists():
            return key


# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_new(request, format=None):
    try:
        user = User.objects.get(username=request.data['primaryUser'])

        request.data.update({'primaryUser': user.id})
        request.data.update({'key': generate_key()})

        if user == request.user:
            if Pusher.objects.filter(primaryUser=user, name=request.data['name']).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = PusherSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_func(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['key'])
    except Pusher.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # if requesting user doesn't have access to the pusher env
    if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        serializer = PusherSerializer(pusher)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = PusherSerializer(pusher, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_204_NO_CONTENT)

    elif request.method == 'DELETE':
        pusher.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# -------------------------------------------- PUSHER ACCESS ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_access_new(request, format=None):
    try:
        user = User.objects.get(username=request.data['username'])
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user access not already in AND requesting user has access to the pusher
        if (not PusherAccess.objects.filter(user=user, pusher=pusher).exists()) and \
                PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'user': user.id, 'pusher': pusher.id})

            # add user access to pusher
            serializer = PusherAccessSerializer(data=request.data)
            if serializer.is_valid():

                serializer.save()
                serializer_data = serializer.data
                for data in serializer_data:
                    data['user'] = user.username
                    data['pusher'] = "[" + pusher.primaryUser.username + "]-" + pusher.name
                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, User.DoesNotExist) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_access_all(request, format=None):
    pusher_access = PusherAccess.objects.filter(user=request.user)
    serializer = PusherAccessSerializer(data=pusher_access, many=True)

    # TODO return primaryUser
    if not serializer.is_valid():  # fixme idk why this not valid
        # serializer.save()
        serializer_data = serializer.data
        for data in serializer_data:
            user = User.objects.get(id=data['user'])
            pusher = Pusher.objects.get(id=data['pusher'])
            data['user'] = user.username
            data['pusher'] = "[" + pusher.primaryUser.username + "]-" + pusher.name
        return Response(serializer_data)
    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_access_func(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # getting all users who have access to pusher
        if request.method == 'GET':
            pusher_access = PusherAccess.objects.filter(pusher=pusher)
            serializer = PusherAccessSerializer(data=pusher_access, many=True)
            if not serializer.is_valid():  # fixme idk why this not valid
                serializer_data = serializer.data
                for data in serializer_data:
                    user = User.objects.get(id=data['user'])
                    pusher = Pusher.objects.get(id=data['pusher'])
                    data['user'] = user.username
                    data['pusher'] = "[" + pusher.primaryUser.username + "]-" + pusher.name
                return Response(serializer_data)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            try:
                # only delete if requesting user is not primary user of pusher
                user = User.objects.get(username=request.data['username'])

                if pusher.primaryUser == user:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)

                if user != request.user:
                    pusher_access = PusherAccess.objects.get(pusher=pusher, user=user)
                    pusher_access.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except PusherAccess.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    except (Pusher.DoesNotExist, User.DoesNotExist, KeyError):
        return Response(status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------- BUDGET ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def entity_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if Budget.objects.filter(pusher=pusher, name=request.data['name']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'pusher': pusher.id})

            # add budget to pusher
            serializer = BudgetSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data
                serializer_data['pusher'] = pusher.name
                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    except (Pusher.DoesNotExist, Budget.DoesNotExist, KeyError) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def budget_func(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        request.data.update({'pusher': pusher.id})

        # getting all users who have access to pusher
        if request.method == 'GET':
            budget = Budget.objects.filter(pusher=pusher)
            serializer = BudgetSerializer(data=budget, many=True)
            if not serializer.is_valid():  # fixme idk why this not valid
                serializer_data = serializer.data
                for data in serializer_data:
                    data['pusher'] = pusher.name
                return Response(serializer_data)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':
            budget = Budget.objects.get(pusher=pusher, name=request.data['name'])
            request.data.update({'id': budget.id})
            serializer = BudgetSerializer(data=request.data)
            if serializer.is_valid():
                # delete old, replace with new
                budget = Budget.objects.get(pusher=request.data['pusher'], name=request.data['name'])
                budget.delete()
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            budget = Budget.objects.filter(pusher=request.data['pusher'], name=request.data['name'])
            budget.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except (Pusher.DoesNotExist, Budget.DoesNotExist, KeyError) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def budget_value_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if not Budget.objects.filter(pusher=pusher, name=request.data['budget']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        budget = Budget.objects.get(pusher=pusher, name=request.data['budget'])

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'budget': budget.id})

            # add budget to pusher
            serializer = BudgetValueSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data
                serializer_data['budget'] = budget.name
                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, Budget.DoesNotExist, TypeError) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def budget_value_all(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if not Budget.objects.filter(pusher=pusher, name=request.data['budget']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        budget = Budget.objects.get(pusher=pusher, name=request.data['budget'])

        budget_values = BudgetValue.objects.filter(budget=budget)

        serializer = BudgetValueSerializer(data=budget_values, many=True)
        if not serializer.is_valid():  # fixme idk why this not valid
            serializer_data = serializer.data
            for data in serializer_data:
                data['budget'] = budget.name
            return Response(serializer_data)
        return Response(data=serializer.errors, status=status.HTTP_404_NOT_FOUND)

    except (Pusher.DoesNotExist, Budget.DoesNotExist, TypeError) as e:
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


# -------------------------------------------- FUND ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def fund_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if Fund.objects.filter(pusher=pusher, name=request.data['name']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # if user access not already in AND requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'pusher': pusher.id})

            # add fund to pusher
            serializer = FundSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, Fund.DoesNotExist) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def fund_func(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        request.data.update({'pusher': pusher.id})

        # getting all funds
        if request.method == 'GET':
            fund = Fund.objects.filter(pusher=pusher)
            serializer = FundSerializer(data=fund, many=True)
            if not serializer.is_valid():  # fixme idk why this not valid
                serializer_data = serializer.data
                for data in serializer_data:
                    data['pusher'] = pusher.name
                return Response(serializer.data)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # editing funds
        elif request.method == 'PUT':
            fund = Fund.objects.get(pusher=request.data['pusher'], name=request.data['name'])
            request.data.update({'id': fund.id})
            serializer = FundSerializer(data=request.data)
            if serializer.is_valid():
                # delete old, replace with new
                fund = Fund.objects.get(pusher=request.data['pusher'], name=request.data['name'])
                fund.delete()
                serializer.save()
                return Response(serializer.data)
            Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # deleting funds
        elif request.method == 'DELETE':
            fund = Fund.objects.filter(pusher=request.data['pusher'], name=request.data['name'])
            fund.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except (Pusher.DoesNotExist, Fund.DoesNotExist) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def fund_value_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if not Fund.objects.filter(pusher=pusher, name=request.data['fund']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        fund = Fund.objects.get(pusher=pusher, name=request.data['fund'])

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'fund': fund.id})

            # add budget to pusher
            serializer = FundValueSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data
                serializer_data['fund'] = fund.name
                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, Budget.DoesNotExist, TypeError) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def fund_value_all(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if not Fund.objects.filter(pusher=pusher, name=request.data['fund']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        fund = Fund.objects.get(pusher=pusher, name=request.data['fund'])

        fund_values = FundValue.objects.filter(fund=fund)

        serializer = FundValueSerializer(data=fund_values, many=True)
        if not serializer.is_valid():  # fixme idk why this not valid
            serializer_data = serializer.data
            for data in serializer_data:
                data['fund'] = fund.name
            return Response(serializer_data)
        return Response(data=serializer.errors, status=status.HTTP_404_NOT_FOUND)

    except (Pusher.DoesNotExist, Fund.DoesNotExist, TypeError) as e:
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


# -------------------------------------------- INCOME ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def income_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])
        user = User.objects.get(username=request.data['username'])

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'pusher': pusher.id})
            request.data.update({'user': user.id})

            # add budget to pusher
            serializer = IncomeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data

                user = User.objects.get(id=serializer_data['user'])
                serializer_data['pusher'] = pusher.name
                serializer_data['user'] = user.first_name + " " + user.last_name
                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, Budget.DoesNotExist, TypeError) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def income_func(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        request.data.update({'pusher': pusher.id})

        # getting all users who have access to pusher
        if request.method == 'GET':
            income = Income.objects.filter(pusher=pusher)
            serializer = IncomeSerializer(data=income, many=True)
            if not serializer.is_valid():  # fixme idk why this not valid
                serializer_data = serializer.data
                for data in serializer_data:
                    user = User.objects.get(id=data['user'])
                    data['pusher'] = pusher.name
                    data['user'] = user.first_name + " " + user.last_name
                return Response(serializer_data)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # delete income
        elif request.method == 'DELETE':
            income = Income.objects.filter(pusher=pusher, timestamp=request.data['timestamp'])
            income.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except (Pusher.DoesNotExist, Income.DoesNotExist) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------- EXPENSE ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def expense_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])
        user = User.objects.get(username=request.data['username'])

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'pusher': pusher.id})
            request.data.update({'user': user.id})

            if Fund.objects.filter(pusher=pusher, name=request.data['fund']).exists():
                fund = Fund.objects.get(pusher=pusher, name=request.data['fund'])
                request.data.update({'fund': fund.id})
            if Budget.objects.filter(pusher=pusher, name=request.data['budget']).exists():
                budget = Budget.objects.get(pusher=pusher, name=request.data['budget'])
                request.data.update({'budget': budget.id})

            # add budget to pusher
            serializer = ExpenseSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data

                # if fund or budget isn't null, replace with the name of fund/budget
                expense = Expense.objects.get(pusher=pusher, timestamp=serializer_data['timestamp'])
                if not expense.budget is None:
                    serializer_data['budget'] = expense.budget.name
                if not expense.fund is None:
                    serializer_data['fund'] = expense.fund.name

                user = User.objects.get(id=serializer_data['user'])
                serializer_data['pusher'] = pusher.name
                serializer_data['user'] = user.first_name + " " + user.last_name
                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, Budget.DoesNotExist, TypeError) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def expense_func(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        request.data.update({'pusher': pusher.id})

        # getting all users who have access to pusher
        if request.method == 'GET':
            expense = Expense.objects.filter(pusher=pusher)
            serializer = ExpenseSerializer(data=expense, many=True)
            if not serializer.is_valid():  # fixme idk why this not valid
                serializer_data = serializer.data
                for data in serializer_data:
                    # if fund or budget isn't null, replace with the name of fund/budget
                    expense = Expense.objects.get(pusher=pusher, timestamp=data['timestamp'])
                    if not expense.budget is None:
                        data['budget'] = expense.budget.name
                    if not expense.fund is None:
                        data['fund'] = expense.fund.name

                    user = User.objects.get(id=data['user'])
                    data['pusher'] = pusher.name
                    data['user'] = user.first_name + " " + user.last_name

                return Response(serializer_data)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # delete expense
        elif request.method == 'DELETE':
            expense = Expense.objects.filter(pusher=pusher, timestamp=request.data['timestamp'])
            expense.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except (Pusher.DoesNotExist, Expense.DoesNotExist) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------- PAYCHECK ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def paycheck_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])
        user = User.objects.get(username=request.data['username'])

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'pusher': pusher.id})
            request.data.update({'user': user.id})
            # request.data.update({'income': })

            # add budget to pusher
            serializer = PaycheckSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data

                serializer_data['pusher'] = pusher.name
                serializer_data['user'] = user.first_name + " " + user.last_name
                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, Paycheck.DoesNotExist, TypeError) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def paycheck_func(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        request.data.update({'pusher': pusher.id})

        # getting all users who have access to pusher
        if request.method == 'GET':
            paycheck = Paycheck.objects.filter(pusher=pusher)
            serializer = PaycheckSerializer(data=paycheck, many=True)
            if not serializer.is_valid():  # fixme idk why this not valid
                serializer_data = serializer.data
                for data in serializer_data:
                    user = User.objects.get(id=data['user'])
                    data['pusher'] = pusher.name
                    data['user'] = user.first_name + " " + user.last_name

                return Response(serializer_data)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # delete income (which in turn deletes paycheck)
        elif request.method == 'DELETE':
            income = Income.objects.get(pusher=pusher, timestamp=request.data['timestamp'])
            income.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except (Pusher.DoesNotExist, Income.DoesNotExist, Paycheck.DoesNotExist, TypeError) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------- PAYCHECK ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def profit_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'pusher': pusher.id})

            # add budget to pusher
            serializer = ProfitSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data

                serializer_data['pusher'] = pusher.name
                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, Profit.DoesNotExist, TypeError) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def profit_all(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        request.data.update({'pusher': pusher.id})

        profit = Profit.objects.filter(pusher=pusher)
        serializer = ProfitSerializer(data=profit, many=True)
        if not serializer.is_valid():  # fixme idk why this not valid
            serializer_data = serializer.data
            for data in serializer_data:
                data['pusher'] = pusher.name
            return Response(serializer_data)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except (Pusher.DoesNotExist, Income.DoesNotExist, Paycheck.DoesNotExist, TypeError) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------- ACCOUNT -----------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def account_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if Account.objects.filter(pusher=pusher, name=request.data['name']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'pusher': pusher.id})

            # add budget to pusher
            serializer = AccountSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data
                serializer_data['pusher'] = pusher.name

                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, Paycheck.DoesNotExist, TypeError) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def account_func(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # getting all users who have access to pusher
        if request.method == 'GET':
            paycheck = Account.objects.filter(pusher=pusher)
            serializer = AccountSerializer(data=paycheck, many=True)
            if not serializer.is_valid():  # fixme idk why this not valid
                serializer_data = serializer.data
                for data in serializer_data:
                    data['pusher'] = pusher.name

                return Response(serializer_data)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # delete income (which in turn deletes paycheck)
        elif request.method == 'DELETE':
            account = Account.objects.get(pusher=pusher, name=request.data['account'])
            account.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except (Pusher.DoesNotExist, Account.DoesNotExist, TypeError) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def account_value_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if not Account.objects.filter(pusher=pusher, name=request.data['account']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            account = Account.objects.get(pusher=pusher, name=request.data['account'])
            request.data.update({'account': account.id})

            # add budget to pusher
            serializer = AccountValueSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data
                serializer_data['account'] = account.name
                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, Account.DoesNotExist, TypeError) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def account_value_all(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if not Account.objects.filter(pusher=pusher, name=request.data['account']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        account = Account.objects.get(pusher=pusher, name=request.data['account'])

        account_values = AccountValue.objects.filter(account=account)

        serializer = AccountValueSerializer(data=account_values, many=True)
        if not serializer.is_valid():  # fixme idk why this not valid
            serializer_data = serializer.data
            for data in serializer_data:
                data['account'] = account.name
            return Response(serializer_data)
        return Response(data=serializer.errors, status=status.HTTP_404_NOT_FOUND)

    except (Pusher.DoesNotExist, Account.DoesNotExist, TypeError) as e:
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


# -------------------------------------------- EXPENDABLE NET WORTH -----------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def exp_net_worth_new(request, format=None):
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if requesting user has access to the pusher
        if PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():

            request.data.update({'pusher': pusher.id})

            # add budget to pusher
            serializer = ExpNetWorthSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer_data = serializer.data
                serializer_data['pusher'] = pusher.name

                return Response(data=serializer_data)

            # if bad format
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # requesting user not authorized to edit
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    except (Pusher.DoesNotExist, ExpNetWorth.DoesNotExist, TypeError) as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def exp_net_worth_all(request, format=None):
    # if call is accurate
    try:
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        # if user has access to the pusher, continue
        if not PusherAccess.objects.filter(user=request.user, pusher=pusher).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        net_worth = ExpNetWorth.objects.filter(pusher=pusher)
        serializer = ExpNetWorthSerializer(data=net_worth, many=True)
        if not serializer.is_valid():  # fixme idk why this not valid
            serializer_data = serializer.data
            for data in serializer_data:
                data['pusher'] = pusher.name

            return Response(serializer_data)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except (Pusher.DoesNotExist, ExpNetWorth.DoesNotExist, TypeError) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)
