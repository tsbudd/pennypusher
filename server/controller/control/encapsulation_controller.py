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
        encapsulation_type = request.data['type']
        name = request.data['name']
        user = request.data

        pusher = handle_valid_request(pusher_key, encapsulation_type, user)
        if isinstance(pusher, Response):
            return pusher

        if encapsulation_exists(encapsulation_type, name, pusher):
            return custom_response("The " + encapsulation_type + " [" + name + "] already exists.",
                                   status.HTTP_400_BAD_REQUEST)

        # retrieving the pusher and other data
        request_data = request.data['data']
        request_data.update({'pusher': pusher.id, 'user': user.id, 'name': name})

        # handling POST
        return handle_ingestion(encapsulation_type, pusher, request_data)

    except TypeError:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def encapsulation_func(request, format=None):
    # if call is accurate
    try:
        if request.method == 'PUT':
            pusher_key = request.data['pusher_key']
            encapsulation_type = request.data['type']
        else:
            pusher_key = request.GET.get('pusher_key')
            encapsulation_type = request.GET.get('type')
        user = request.user

        pusher = handle_valid_request(pusher_key, encapsulation_type, user)
        if isinstance(pusher, Response):
            return pusher

        if request.method == 'GET':
            # get all data
            entity_data = get_entity_list(encapsulation_type, pusher)
            serializer = get_serializer(encapsulation_type, entity_data, True)

            if not serializer.is_valid():
                serializer_data = serializer.data
                return Response(data=serializer_data)
            else:
                return custom_response("Invalid encapsulation_type: " + encapsulation_type,
                                       status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':

            # fixme i think i can make this a function call
            name = request.data['name']
            if not encapsulation_exists(encapsulation_type, name, pusher):
                return custom_response("The " + encapsulation_type + " [" + name + "] does not exist.",
                                       status.HTTP_400_BAD_REQUEST)

            # encapsulation = get_encapsulation(encapsulation_type, encapsulation_name)
            request_data = request.data['data']
            request_data.update({'name': name, 'pusher': pusher.id})

            # handle_ingestion
            serializer = get_serializer(encapsulation_type, request_data, False)
            if serializer.is_valid():
                # encapsulation.delete()
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            name = request.GET.get('name')
            if not encapsulation_exists(encapsulation_type, name, pusher):
                return custom_response("The " + encapsulation_type + " [" + name + "] does not exist.",
                                       status.HTTP_400_BAD_REQUEST)
            encapsulation = get_encapsulation(encapsulation_type, name, pusher)
            encapsulation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except TypeError:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def encapsulation_value_new(request, format=None):
    try:
        pusher_key = request.data['pusher_key']
        e_type = request.data['type']
        user = request.user

        pusher = handle_valid_request(pusher_key, e_type, user)
        if isinstance(pusher, Response):
            return pusher

        # retrieving the pusher and other data
        request_data = request.data
        request_data.update({'pusher': pusher.id})

        return handle_ingestion(e_type, pusher, request_data)

    except KeyError:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def encapsulation_value_func(request, format=None):
    try:
        pusher_key = request.GET.get('pusher_key')
        e_type = request.GET.get('type')
        user = request.user

        pusher = handle_valid_request(pusher_key, e_type, user)
        if isinstance(pusher, Response):
            return pusher

        encapsulation_name = request.GET.get('name')
        if not encapsulation_exists(e_type, encapsulation_name, pusher):
            return custom_response("The " + e_type + " [" + encapsulation_name + "] does not exist.",
                                   status.HTTP_400_BAD_REQUEST)

        encapsulation = get_encapsulation(e_type, encapsulation_name, pusher)

        if request.method == 'GET':
            # get page of data
            paginator = ResponsePagination()
            entity_data = get_encapsulation_value_list(e_type, encapsulation.id)

            # Paginate the queryset before serializing it
            result_page = paginator.paginate_queryset(entity_data, request)
            serializer = get_serializer(e_type + '_value', result_page, True)

            if not serializer.is_valid():
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            timestamp = request.GET.get('timestamp')
            date_object = datetime.fromisoformat(timestamp[:-1])
            if not encapsulation_value_exists(e_type, encapsulation.id, date_object):
                return custom_response("The " + e_type + " value at  [" + timestamp +
                                       "] does not exist.", status.HTTP_400_BAD_REQUEST)

            encapsulation_value = get_encapsulation_value(e_type, encapsulation.id, date_object)
            encapsulation_value.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except TypeError:
        return Response(status=status.HTTP_400_BAD_REQUEST)
