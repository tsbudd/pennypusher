from server.controller.control.views_helper import *
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination


class ResponsePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'


# -------------------------------------------- BUDGET ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def encapsulation_new(request, format=None):
    try:
        pusher_key = request.data['pusher_key']
        entity_type = request.data['entity_type']
        user = request.user

        if not pusher_exists(pusher_key):
            return failure_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)
        if not user_has_access(user, request.data['pusher_key']):
            return failure_response("The user " + user + " does not have access to the pusher.",
                                    status.HTTP_401_UNAUTHORIZED)
        if not encapsulation_type_exists(entity_type):
            return failure_response("The type " + entity_type + " is not allowed.", status.HTTP_400_BAD_REQUEST)

        entity_name = request.data['entity_name']
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if not encapsulation_exists(entity_type, entity_name, pusher):
            return failure_response("The " + entity_type + " " + entity_name + " already exists.",
                                    status.HTTP_400_BAD_REQUEST)

        # retrieving the pusher and other data
        request_data = request.data['data']
        request_data.update({'pusher': pusher.id})
        request_data.update({'user': user.id})

        serializer = get_serializer(entity_type, request_data, False)
        if serializer.is_valid():
            serializer.save()
            serializer_data = serializer.data
            return Response(data=serializer_data)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except KeyError as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def encapsulation_func(request, format=None):
    # if call is accurate
    try:
        pusher_key = request.GET.get('pusher_key')
        entity_type = request.GET.get('entity_type')
        user = request.user

        if not pusher_exists(pusher_key):
            return failure_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)
        if not user_has_access(user, request.data['pusher_key']):
            return failure_response("The user " + user + " does not have access to the pusher.",
                                    status.HTTP_401_UNAUTHORIZED)
        if not entity_type_exists(entity_type):
            return failure_response("The type " + entity_type + " is not allowed.", status.HTTP_400_BAD_REQUEST)

        if request.method == 'GET':
            pusher = Pusher.objects.get(key=request.data['pusher_key'])

            # get all data
            paginator = ResponsePagination()
            entity_data = get_entity_list(entity_type, pusher)
            serializer = get_serializer(entity_type, entity_data, True)

            if serializer.is_valid():
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':
            entity_id = request.data['entity_id']
            entity = get_entity(entity_type, entity_id)
            request.data.update({'id': entity.id})
            serializer = get_serializer(entity_type, entity, False)
            if serializer.is_valid():
                # delete old, replace with new
                entity.delete()
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            entity_id = request.GET.get('entity_id')
            entity = get_entity(entity_type, entity_id)
            entity.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except (Pusher.DoesNotExist, Budget.DoesNotExist, KeyError) as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def encapsulation_value_new(request, format=None):
    try:
        pusher_key = request.data['pusher_key']
        entity_type = request.data['entity_type']
        user = request.user

        if not pusher_exists(pusher_key):
            return failure_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)
        if not user_has_access(user, request.data['pusher_key']):
            return failure_response("The user " + user + " does not have access to the pusher.",
                                    status.HTTP_401_UNAUTHORIZED)
        if not encapsulation_type_exists(entity_type):
            return failure_response("The type " + entity_type + " is not allowed.", status.HTTP_400_BAD_REQUEST)

        entity_name = request.data['entity_name']
        pusher = Pusher.objects.get(key=request.data['pusher_key'])

        if not encapsulation_exists(entity_type, entity_name, pusher):
            return failure_response("The " + entity_type + " " + entity_name + " already exists.",
                                    status.HTTP_400_BAD_REQUEST)

        # retrieving the pusher and other data
        request_data = request.data['data']
        request_data.update({'pusher': pusher.id})
        request_data.update({'user': user.id})

        serializer = get_serializer(entity_type, request_data, False)
        if serializer.is_valid():
            serializer.save()
            serializer_data = serializer.data
            return Response(data=serializer_data)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except KeyError as e:
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
