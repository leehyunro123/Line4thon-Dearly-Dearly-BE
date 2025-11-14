from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import Notice
from .serializers import NoticeSerializer


# Create your views here.
@api_view(['GET','POST'])
@parser_classes([JSONParser,MultiPartParser, FormParser])
def notice_list(request):
    if request.method == 'GET':
        qs = Notice.objects.all()
        serializer = NoticeSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    if not request.user.is_authenticated or not request.user.is_staff:
        return Response(
            {'detail': '공지 작성 권한이 없습니다.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = NoticeSerializer(data=request.data)
    if serializer.is_valid():
        notice = serializer.save()
        out_ser = NoticeSerializer(notice)
        return Response(out_ser.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def latest_notice(request):
    notice=Notice.objects.order_by('-created_at').first()
    if not notice:
        return Response(
            {'detail':'공지사항이 없습니다.'},
            status = status.HTTP_404_NOT_FOUND
        )
    serializer = NoticeSerializer(notice)
    return Response(serializer.data, status.HTTP_200_OK)

@api_view(['GET'])
def has_new_notice(request):
    #프론트에서 마지막으로 본 공지 id를 last_seen_id로 보내면, 
    # 그 이후에 새 공지가 있는지 알려줌
    # ex. GET /notices/has_new?last_seen_id=3

    last_seen_id = request.query_params.get('last_seen_id')

    latest = Notice.objects.order_by('-id').first()
    if not latest:
        return Response({'has_new':False, 'latest_id':None})
    
    if not last_seen_id:
        return Response({'has_new':True, 'latest_id':latest.id})
    
    try:
        last_seen_id = int(last_seen_id)
    except ValueError:
        return Response({'detail': 'last_seen_id는 정수여야 합니다.'},
                        status=status.HTTP_400_BAD_REQUEST)

    has_new = latest.id > last_seen_id
    return Response({'has_new': has_new, 'latest_id': latest.id})

@api_view(['GET'])
def notice_detail(request, notice_id):
    try:
        notice = Notice.objects.get(id=notice_id)
    except Notice.DoesNotExist:
        return Response(
            {'detail': '공지사항이 존재하지 않습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = NoticeSerializer(notice)
    return Response(serializer.data, status=status.HTTP_200_OK)
