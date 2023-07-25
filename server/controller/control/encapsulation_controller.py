from datetime import datetime

from rest_framework.exceptions import ValidationError

from .views_helper import *
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
        encapsulation_type = request.data['encapsulation_type']
        user = request.user

        if not pusher_exists(pusher_key):
            return failure_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)
        pusher = Pusher.objects.get(key=request.data['pusher_key'])
        if not user_has_access(user, pusher):
            return failure_response("The user " + user + " does not have access to the pusher.",
                                    status.HTTP_401_UNAUTHORIZED)
        if not encapsulation_type_exists(encapsulation_type):
            return failure_response("The type " + encapsulation_type + " is not allowed.", status.HTTP_400_BAD_REQUEST)

        name = request.data['encapsulation_name']

        if encapsulation_exists(encapsulation_type, name, pusher):
            return failure_response("The " + encapsulation_type + " [" + name + "] already exists.",
                                    status.HTTP_400_BAD_REQUEST)

        # retrieving the pusher and other data
        request_data = request.data['data']
        request_data.update({'name': name})
        request_data.update({'pusher': pusher.id})
        request_data.update({'user': user.id})

        # Get the serializer for the specified encapsulation_type
        serializer = get_serializer(encapsulation_type, request_data, False)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data)
        else:
            return failure_response("Invalid encapsulation_type: " + encapsulation_type,
                                    status.HTTP_400_BAD_REQUEST)
    except TypeError as e:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def encapsulation_func(request, format=None):
    # if call is accurate
    try:
        if request.method == 'GET' or request.method == 'DELETE':
            pusher_key = request.GET.get('pusher_key')
            encapsulation_type = request.GET.get('encapsulation_type')
        else:
            pusher_key = request.data['pusher_key']
            encapsulation_type = request.data['encapsulation_type']
        user = request.user

        if not pusher_exists(pusher_key):
            return failure_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)

        pusher = Pusher.objects.get(key=pusher_key)
        if not user_has_access(user, pusher):
            return failure_response("The user " + user + " does not have access to the pusher.",
                                    status.HTTP_401_UNAUTHORIZED)
        if not entity_type_exists(encapsulation_type):
            return failure_response("The type [" + encapsulation_type + "] is not allowed.", status.HTTP_400_BAD_REQUEST)

        if request.method == 'GET':
            # get all data
            entity_data = get_entity_list(encapsulation_type, pusher)
            serializer = get_serializer(encapsulation_type, entity_data, True)
            if not serializer.is_valid():
                serializer_data = serializer.data
                return Response(data=serializer_data)
            else:
                return failure_response("Invalid encapsulation_type: " + encapsulation_type,
                                        status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':
            encapsulation_name = request.data['encapsulation_name']
            if not encapsulation_exists(encapsulation_type, encapsulation_name, pusher):
                return failure_response("The "+encapsulation_type+" [" + encapsulation_name + "] does not exist.",
                                        status.HTTP_400_BAD_REQUEST)

            encapsulation = get_encapsulation(encapsulation_type, encapsulation_name)
            request_data = request.data['data']
            request_data.update({'name': encapsulation_name})
            request_data.update({'pusher': pusher.id})
            serializer = get_serializer(encapsulation_type, request_data, False)
            if serializer.is_valid():
                encapsulation.delete()
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            encapsulation_name = request.GET.get('encapsulation_name')
            if not encapsulation_exists(encapsulation_type, encapsulation_name, pusher):
                return failure_response("The " + encapsulation_type + " [" + encapsulation_name + "] does not exist.",
                                        status.HTTP_400_BAD_REQUEST)
            encapsulation = get_encapsulation(encapsulation_type, encapsulation_name)
            encapsulation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except User.DoesNotExist as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def encapsulation_value_new(request, format=None):
    try:
        pusher_key = request.data['pusher_key']
        encapsulation_type = request.data['encapsulation_type']
        user = request.user

        if not pusher_exists(pusher_key):
            return failure_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)
        pusher = Pusher.objects.get(key=request.data['pusher_key'])
        if not user_has_access(user, pusher):
            return failure_response("The user " + user + " does not have access to the pusher.",
                                    status.HTTP_401_UNAUTHORIZED)
        if not encapsulation_type_exists(encapsulation_type):
            return failure_response("The type " + encapsulation_type + " is not allowed.", status.HTTP_400_BAD_REQUEST)

        encapsulation_name = request.data['encapsulation_name']

        if not encapsulation_exists(encapsulation_type, encapsulation_name, pusher):
            return failure_response("The " + encapsulation_type + " [" + encapsulation_name + "] does not exist.",
                                    status.HTTP_400_BAD_REQUEST)

        encapsulation_value_type = encapsulation_type+"_value"
        encapsulation = get_encapsulation(encapsulation_type, encapsulation_name)

        # retrieving the pusher and other data
        request_data = request.data
        request_data.update({encapsulation_type: encapsulation.id})

        serializer = get_serializer(encapsulation_value_type, request_data, False)
        if serializer.is_valid():
            serializer.save()
            serializer_data = serializer.data
            return Response(data=serializer_data)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except TypeError as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def encapsulation_value_func(request, format=None):
    try:
        pusher_key = request.GET.get('pusher_key')
        encapsulation_type = request.GET.get('encapsulation_type')
        user = request.user

        if not pusher_exists(pusher_key):
            return failure_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)
        pusher = Pusher.objects.get(key=pusher_key)
        if not user_has_access(user, pusher):
            return failure_response("The user " + user + " does not have access to the pusher.",
                                    status.HTTP_401_UNAUTHORIZED)
        if not encapsulation_type_exists(encapsulation_type):
            return failure_response("The type " + encapsulation_type + " is not allowed.", status.HTTP_400_BAD_REQUEST)

        encapsulation_name = request.GET.get('encapsulation_name')
        if not encapsulation_exists(encapsulation_type, encapsulation_name, pusher):
            return failure_response("The " + encapsulation_type + " [" + encapsulation_name + "] does not exist.",
                                    status.HTTP_400_BAD_REQUEST)

        encapsulation = get_encapsulation(encapsulation_type, encapsulation_name)

        if request.method == 'GET':
            encapsulation_value_type = encapsulation_type+'_value'
            # get all data
            entity_data = get_encapsulation_value_list(encapsulation_type, encapsulation.id)
            serializer = get_serializer(encapsulation_value_type, entity_data, True)

            if not serializer.is_valid():
                return Response(data=serializer.data)
            else:
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            encapsulation_timestamp = request.GET.get('encapsulation_value_timestamp')
            if encapsulation_type == 'account':
                date_object = datetime.fromisoformat(encapsulation_timestamp[:-1])
            else:
                date_object = datetime.strptime(encapsulation_timestamp, '%Y-%m-%d').date()
            if not encapsulation_value_exists(encapsulation_type, encapsulation.id, date_object):
                return failure_response("The " + encapsulation_type + " value at  [" + encapsulation_timestamp +
                                        "] does not exist.", status.HTTP_400_BAD_REQUEST)

            encapsulation_value = get_encapsulation_value(encapsulation_type, encapsulation.id, date_object)
            encapsulation_value.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except User.DoesNotExist as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)
