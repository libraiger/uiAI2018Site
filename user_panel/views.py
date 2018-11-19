from django.http import HttpResponse
from rest_framework.status import *
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from user_panel.models import *
from user_panel.decorators import *


@api_view(['GET'])
@permission_classes([AllowAny])
def get_settings(request):
    return Response(dict((s.key, s.value) for s in Settings.objects.all()))


@api_view(['POST'])
@permission_classes([AllowAny])
def sign_up(request):
    try:
        User.objects.create_user(
            email=request.data.get('email'),
            password=request.data.get('password'),
            first_name=request.data.get('first_name'),
            last_name=request.data.get('last_name'),
            phone=request.data.get('phone'),
            institute=request.data.get('institute'),
            english_full_name=request.data.get('english_full_name')
        )
        return Response({'message': 'ثبت‌نام با موفقیت انجام شد.'}, status=HTTP_201_CREATED)
    except ValidationError as e:
        return Response({'message': str(e.message)}, status=HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_user_info(request):
    user = request.user
    return Response(user.get_dict())


@api_view(['POST'])
def edit_user_info(request):
    try:
        request.user.email = request.data.get('email')
        request.user.first_name = request.data.get('first_name')
        request.user.last_name = request.data.get('last_name')
        request.user.phone = request.data.get('phone')
        request.user.institute = request.data.get('institute')
        request.user.english_full_name = request.data.get('english_full_name')
        request.user.save()
        return Response({'message': 'اطلاعات شما ویرایش شد.'})
    except ValidationError as e:
        return Response({'message': str(e.message)}, status=HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_team(request):
    team_name = request.data.get('name')
    if not team_name:
        return Response({'message': 'نام تیم نمی‌تواند خالی باشد.'}, status=HTTP_400_BAD_REQUEST)
    try:
        validators.team_name_validator(team_name)
        if request.user.team is not None:
            request.user.team.name = team_name
            request.user.team.save()
            return Response({'message': 'نام تیم شما به {} تغییر یافت.'.format(request.user.team.name)},
                            status=HTTP_200_OK)
        else:
            team = Team(name=team_name)
            team.save()
            request.user.team = team
            request.user.save()
            return Response({'message': 'تیم {} با موفقیت ساخته شد.'.format(request.user.team.name)},
                            status=HTTP_201_CREATED)
    except ValidationError as e:
        return Response({'message': str(e.message)}, status=HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
@team_required
def get_team_info(request):
    if not request.user.is_authenticated and 'team_id' not in request.data:
        return Response({'message': 'کد تیم مشخص نشده.'}, status=HTTP_400_BAD_REQUEST)
    team_id = int(request.data.get('team_id', request.user.team.pk))
    try:
        team = Team.objects.get(pk=team_id)
        return Response(team.get_dict())
    except Team.DoesNotExist:
        return Response({'message': 'تیم مورد نظر پیدا نشد.'}, status=HTTP_404_NOT_FOUND)


@api_view(['POST'])
@team_required
def send_team_invitation(request):
    receiver_email = request.data.get('email')
    try:
        receiver = User.objects.get(email=receiver_email)
        TeamInvitation(
            sender=request.user,
            receiver=receiver,
            team=request.user.team,
        ).save()
        return Response({'message': 'دعوت‌نامه به کاربر مورد نظر ارسال شد.'}, status=HTTP_201_CREATED)
    except User.DoesNotExist:
        return Response({'message': 'کاربر با ایمیل مورد نظر پیدا نشد.'}, status=HTTP_404_NOT_FOUND)


@api_view(['POST'])
def accept_team_invitation(request):
    if request.user.team is not None:
        return Response({'message': 'شما در یک تیم عضو هستید و نمی‌توانید دعوت‌نامه‌ای را بپذیرید.'},
                        status=HTTP_403_FORBIDDEN)
    invitation_id = request.data.get('id')
    if not invitation_id or not str(invitation_id).isdecimal():
        return Response({'message': 'شماره دعوت‌نامه اشتباه است.'}, status=HTTP_400_BAD_REQUEST)
    try:
        invitation = TeamInvitation.objects.get(pk=int(invitation_id))
    except TeamInvitation.DoesNotExist:
        return Response({'message': 'دعوت‌نامه مورد نظر یافت نشد.'}, status=HTTP_404_NOT_FOUND)
    if invitation.receiver != request.user:
        return Response({'message': 'این دعوت‌نامه مربوط به شما نیست.'}, status=HTTP_403_FORBIDDEN)
    if invitation.status != TeamInvitation.PENDING:
        return Response({'message': 'دعوت‌نامه فاقد اعتبار است.'}, status=HTTP_403_FORBIDDEN)
    request.user.team = invitation.team
    request.user.save()
    invitation.status = TeamInvitation.ACCEPTED
    invitation.save()
    return Response({'message': 'شما در تیم {} عضو شدید.'.format(invitation.team.name)})


@api_view(['POST'])
def reject_team_invitation(request):
    invitation_id = request.data.get('id')
    if not invitation_id or not str(invitation_id).isdecimal():
        return Response({'message': 'شماره دعوت‌نامه اشتباه است.'}, status=HTTP_400_BAD_REQUEST)
    try:
        invitation = TeamInvitation.objects.get(pk=int(invitation_id))
    except TeamInvitation.DoesNotExist:
        return Response({'message': 'دعوت‌نامه مورد نظر یافت نشد.'}, status=HTTP_404_NOT_FOUND)
    if invitation.receiver != request.user:
        return Response({'message': 'این دعوت‌نامه مربوط به شما نیست.'}, status=HTTP_403_FORBIDDEN)
    if invitation.status != TeamInvitation.PENDING:
        return Response({'message': 'دعوت‌نامه فاقد اعتبار است.'}, status=HTTP_403_FORBIDDEN)
    invitation.status = TeamInvitation.REJECTED
    invitation.save()
    return Response({'message': 'دعوت به عضویت در تیم {} رد شد.'.format(invitation.team.name)})


@api_view(['POST'])
@team_required
def leave_team(request):
    team_name = request.user.team.name
    request.user.team = None
    request.user.save()
    return Response({'message': 'عضویت شما در تیم {} لغو شد.'.format(team_name)})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_version(request):
    """
    suggested names: server, client_python, client_java, client_cpp
    """
    requester = request.GET.get('name')
    setting_key = 'version_{}'.format(requester)
    try:
        setting = Settings.objects.get(key=setting_key)
        return Response({'version': setting.value})
    except Settings.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)
