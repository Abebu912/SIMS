from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from notifications.models import Announcement
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_announcements_api(request):
    """API endpoint for student announcements - returns real data from database"""
    try:
        # Get all active announcements first
        all_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
        
        # Filter announcements relevant to the user's role
        relevant_announcements = []
        user_role = request.user.role
        
        for announcement in all_announcements:
            target_roles = getattr(announcement, 'target_roles', [])
            
            # Handle different data types for target_roles
            if isinstance(target_roles, str):
                try:
                    import json
                    target_roles = json.loads(target_roles)
                except:
                    target_roles = [role.strip() for role in target_roles.split(',') if role.strip()]
            elif not isinstance(target_roles, list):
                target_roles = []
            
            # Check if announcement targets this user's role or is for everyone
            if not target_roles or len(target_roles) == 0 or user_role in target_roles:
                relevant_announcements.append({
                    "id": announcement.id,
                    "title": announcement.title,
                    "content": announcement.content,
                    "created_at": announcement.created_at.isoformat(),
                    "is_important": False  # You can add a priority field to Announcement model if needed
                })
        
        return Response({
            "announcements": relevant_announcements,
            "count": len(relevant_announcements),
            "last_updated": timezone.now().isoformat()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "announcements": [],
            "count": 0,
            "error": str(e)
        }, status=500)

@login_required
def student_announcements(request):
    """Render the student announcements page"""
    from notifications.models import Announcement
    
    try:
        # Get all active announcements first
        all_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
        
        # Filter announcements relevant to the user's role
        relevant_announcements = []
        user_role = request.user.role
        
        for announcement in all_announcements:
            target_roles = getattr(announcement, 'target_roles', [])
            
            # Handle different data types for target_roles
            if isinstance(target_roles, str):
                try:
                    import json
                    target_roles = json.loads(target_roles)
                except:
                    target_roles = [role.strip() for role in target_roles.split(',') if role.strip()]
            elif not isinstance(target_roles, list):
                target_roles = []
            
            # Check if announcement targets this user's role or is for everyone
            if not target_roles or len(target_roles) == 0 or user_role in target_roles:
                relevant_announcements.append(announcement)
                
    except Exception as e:
        relevant_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
        print(f"Error filtering announcements: {e}")
    
    context = {
        'page_title': 'School Announcements',
        'announcements': relevant_announcements,
    }
    return render(request, 'students/announcements.html', context)
