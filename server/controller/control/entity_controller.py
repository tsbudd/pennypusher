from datetime import datetime

from django.http import HttpResponse
from rest_framework.pagination import PageNumberPagination
from .views_helper import *
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


class ResponsePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'


def index():
    return HttpResponse("PennyPusher Index")


# -------------------------------------------- ENTITY ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def entity_new(request, format=None):
    try:
        pusher_key = request.data['pusher_key']
        e_type = request.data['type']
        user = request.user

        pusher = handle_valid_request(pusher_key, e_type, user)
        if isinstance(pusher, Response):
            return pusher

        # retrieving the pusher and other data
        request_data = request.data['data']
        request_data.update({'pusher': pusher.id, 'user': user.id, 'type': e_type})

        # handling POST
        return handle_ingestion(e_type, pusher, request_data)

    except KeyError:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE', 'PUT'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def entity_func(request, format=None):
    # if call is accurate
    try:
        if request.method == 'PUT':
            pusher_key = request.data['pusher_key']
            e_type = request.data['type']
        else:
            pusher_key = request.GET.get('pusher_key')
            e_type = request.GET.get('type')
        user = request.user

        pusher = handle_valid_request(pusher_key, e_type, user)
        if isinstance(pusher, Response):
            return pusher

        if request.method == 'GET':
            # get page of data
            paginator = ResponsePagination()
            entity_data = get_entity_list(e_type, pusher)

            # Paginate the queryset before serializing it
            result_page = paginator.paginate_queryset(entity_data, request)
            serializer = get_serializer(e_type, result_page, True)

            if not serializer.is_valid():
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':
            # Electives only
            if e_type not in ['subscription', 'for_sale', 'desired_purchase', 'bill']:
                return custom_response("Entity types of " + e_type + " cannot be modified.",
                                       status.HTTP_400_BAD_REQUEST)

            request_data = request.data['data']
            request_data.update({'pusher': pusher.id, 'user': user.id, 'type': e_type})

            # handling POST
            return handle_modification(e_type, pusher, request_data)

        elif request.method == 'DELETE':
            item, timestamp = "", ""
            if e_type in ['subscription', 'for_sale', 'desired_purchase']:
                item = request.GET.get('item')
                if not elective_exists(e_type, pusher, item):
                    return custom_response("The " + e_type + " [" + item + "] does not exist.",
                                           status.HTTP_400_BAD_REQUEST)
                entity = get_elective(e_type, pusher, item)
            else:
                timestamp = request.GET.get('timestamp')
                date_object = datetime.fromisoformat(timestamp[:-1])
                if not entity_exists(e_type, pusher, date_object):
                    return custom_response("The " + e_type + " at [" + timestamp + "] does not exist.",
                                           status.HTTP_400_BAD_REQUEST)
                entity = get_entity(e_type, pusher, date_object)

            entity.delete()
            if e_type in ['subscription', 'for_sale', 'desired_purchase']:
                return custom_response("Successful deletion of the " + e_type + " [" + item + "].",
                                       status.HTTP_204_NO_CONTENT)
            else:
                return custom_response("Successful deletion of " + e_type + " at [" + timestamp + "].",
                                       status.HTTP_204_NO_CONTENT)

    except KeyError:
        return Response(status=status.HTTP_400_BAD_REQUEST)
