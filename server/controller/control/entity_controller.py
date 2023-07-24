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


def index(request):
    return HttpResponse("PennyPusher Index")

# -------------------------------------------- ENTITY ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def entity_new(request, format=None):
    try:
        pusher_key = request.data['pusher_key']
        entity_type = request.data['entity_type']
        user = request.user

        if not pusher_exists(pusher_key):
            return failure_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)
        if not user_has_access(user, request.data['pusher_key']):
            return failure_response("The user " + user + " does not have access to the pusher.",
                                    status.HTTP_401_UNAUTHORIZED)
        if not entity_type_exists(entity_type):
            return failure_response("The type " + entity_type + " is not allowed.", status.HTTP_400_BAD_REQUEST)

        # retrieving the pusher and other data
        pusher = Pusher.objects.get(key=request.data['pusher_key'])
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

    except TypeError as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def entity_func(request, format=None):
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
            # this_month = request.GET.get('this_month', 'false')

            # get page of data
            paginator = ResponsePagination()
            entity_data = get_entity_list(entity_type, pusher)
            result_page = paginator.paginate_queryset(entity_data, request)
            serializer = get_serializer(entity_type, result_page, True)

            if serializer.is_valid():
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            entity_id = request.GET.get('entity_id')
            entity = get_entity(entity_type, entity_id)
            entity.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except TypeError as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)
