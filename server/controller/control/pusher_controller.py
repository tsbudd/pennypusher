from server.controller.control.views_helper import *
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


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
