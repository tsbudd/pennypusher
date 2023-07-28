from .views_helper import *
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, permissions


# -------------------------------------------- PUSHER ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_all(request, format=None):
    try:
        data = Pusher.objects.filter(primaryUser=request.user)
        serializer = PusherSerializer(data=data, many=True)

        if not serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except TypeError as e:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def pusher_new(request, format=None):
    try:
        user = request.user
        pusher_name = request.data['name']

        if Pusher.objects.filter(primaryUser=user, name=pusher_name).exists():
            return custom_response("The user " + user.username + " already has a pusher called " + pusher_name + ".",
                                   status.HTTP_400_BAD_REQUEST)

        request_data = request.data
        request_data.update({'key': generate_key()})
        request_data.update({'user': user.id})

        serializer = PusherSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except (TypeError, KeyError) as e:
        return custom_response("System Error", status.HTTP_500_INTERNAL_SERVER_ERROR)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_func(request, format=None):
    try:
        pusher_key = ""
        if request.method == 'GET' or request.method == 'DELETE':
            pusher_key = request.GET.get('pusher_key')
        else:
            pusher_key = request.data['key']

        user = request.user

        if not pusher_exists(pusher_key):
            return custom_response("The pusher_key [" + pusher_key + "] is not valid.", status.HTTP_400_BAD_REQUEST)

        pusher = Pusher.objects.get(key=pusher_key)
        if not user_has_access(user, pusher):
            return custom_response("The user [" + user + "] does not have access to the pusher.",
                                   status.HTTP_401_UNAUTHORIZED)

        if request.method == 'GET':
            serializer = PusherSerializer(pusher)
            return Response(serializer.data)

        elif request.method == 'PUT':
            request_data = request.data
            request_data.update({'key': pusher.key})
            request_data.update({'primaryUser': pusher.primaryUser.id})
            serializer = PusherSerializer(pusher, data=request_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            pusher.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except TypeError as e:
        return custom_response("System Error", status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------------------------- PUSHER ACCESS ------------------------------------------
# @limits(key='ip', rate='100/h')
@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_access_new(request, format=None):
    try:
        username = request.data['username']
        pusher_key = request.data['pusher_key']
        request_user = request.user

        if not pusher_exists(pusher_key):
            return custom_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)
        if not user_exists(username):
            return custom_response("The user " + username + " does not exist.", status.HTTP_400_BAD_REQUEST)

        pusher = Pusher.objects.get(key=pusher_key)
        new_user = User.objects.get(username=username)
        if not user_has_access(request_user.id, pusher.id):
            return custom_response("The user " + request_user + " does not have access to the specified pusher.",
                                   status.HTTP_401_UNAUTHORIZED)
        if user_has_access(new_user.id, pusher.id):
            return custom_response("The user " + username + " already has access to the specified pusher.",
                                   status.HTTP_400_BAD_REQUEST)

        new_user = User.objects.get(username=username)

        request.data.update({'user': new_user.id, 'pusher': pusher.id})

        # add user access to pusher
        serializer = PusherAccessSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except TypeError as e:  # if bad format
        return Response(status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_access_all(request, format=None):
    pusher_key = request.GET.get('pusher_key')
    request_user = request.user

    if not pusher_exists(pusher_key):
        return custom_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)

    pusher = Pusher.objects.get(key=pusher_key)
    if not user_has_access(request_user, pusher):
        return custom_response("The user " + request_user + " does not have access to the specified pusher.",
                               status.HTTP_401_UNAUTHORIZED)
    if request.user != pusher.primaryUser:
        return custom_response("The user " + request_user + " is not an admin of the specified pusher.",
                               status.HTTP_401_UNAUTHORIZED)

    # getting all users who have access to pusher
    if request.method == 'GET':
        pusher_access = PusherAccess.objects.filter(pusher=pusher.id)
        serializer = PusherAccessSerializer(data=pusher_access, many=True)
        if not serializer.is_valid():  # fixme idk why this not valid
            return Response(serializer.data)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @limits(key='ip', rate='100/h')
@api_view(['GET', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def pusher_access_func(request, format=None):
    # if call is accurate
    try:
        pusher_key = request.GET.get('pusher_key')
        request_user = request.user

        if not pusher_exists(pusher_key):
            return custom_response("The pusher_key " + pusher_key + " is not valid.", status.HTTP_400_BAD_REQUEST)

        pusher = Pusher.objects.get(key=pusher_key)
        if not user_has_access(request_user, pusher):
            return custom_response("The user " + request_user + " does not have access to the specified pusher.",
                                   status.HTTP_401_UNAUTHORIZED)

        # getting all pushers user has access to
        if request.method == 'GET':
            pusher_access = PusherAccess.objects.filter(user=request_user.id)
            serializer = PusherAccessSerializer(data=pusher_access, many=True)
            if not serializer.is_valid():  # fixme idk why this not valid
                return Response(serializer.data)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            # only delete if requesting user is not primary user of pusher
            username = request.GET.get('username')

            if not user_exists(username):
                return custom_response("The user " + username + " does not exist.", status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(username=username)
            if not user_has_access(user, pusher):
                return custom_response("The user " + username + " does not have access to this pusher.",
                                       status.HTTP_400_BAD_REQUEST)
            if pusher.primaryUser == user:
                return custom_response("You cannot delete yourself from the pusher since you are the primary user",
                                       status.HTTP_401_UNAUTHORIZED)

            if user != request.user:
                pusher_access = PusherAccess.objects.get(pusher=pusher, user=user)
                pusher_access.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    except TypeError as e:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
