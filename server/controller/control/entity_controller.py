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
        request_data.update({'pusher': pusher.id, 'user': user.id})

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
            request_data = request.data['data']
            request_data.update({'pusher': pusher.id, 'user': user.id, 'type': e_type})

            # handling POST
            return handle_ingestion(e_type, pusher, request_data)

        elif request.method == 'DELETE':
            entity_timestamp = request.GET.get('timestamp')
            date_object = datetime.fromisoformat(entity_timestamp[:-1])
            if not entity_exists(e_type, pusher, date_object):
                return custom_response("The " + e_type + " at [" + entity_timestamp + "] does not exist.",
                                       status.HTTP_400_BAD_REQUEST)
            entity = get_entity(e_type, pusher, date_object)
            entity.delete()
            return custom_response("successful deletion", status.HTTP_204_NO_CONTENT)

    except TypeError:
        return Response(status=status.HTTP_400_BAD_REQUEST)
