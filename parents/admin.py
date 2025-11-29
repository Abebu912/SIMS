from django.contrib import admin, messages
from .models import ChildLinkRequest
from users.models import StudentParent, User
from students.models import Student
from django.utils.html import format_html
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings


@admin.register(ChildLinkRequest)
class ChildLinkRequestAdmin(admin.ModelAdmin):
    list_display = ('parent', 'child_identifier', 'relationship', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('parent__username', 'child_identifier', 'parent__email')
    actions = ['approve_requests', 'decline_requests']
    readonly_fields = ('matched_student_info',)

    def matched_student_info(self, obj):
        identifier = (obj.child_identifier or '').strip()
        if not identifier:
            return '-'

        student = Student.objects.filter(student_id__iexact=identifier).first()
        if not student:
            student = Student.objects.filter(user__email__iexact=identifier).first()
        if not student:
            student = Student.objects.filter(user__username__iexact=identifier).first()

        if student:
            url = reverse('admin:students_student_change', args=[student.id])
            return format_html('<a href="{}">{} ({})</a>', url, student.user.get_full_name(), student.student_id)
        return 'No matching student found.'
    matched_student_info.short_description = 'Matched student'

    def approve_requests(self, request, queryset):
        approved = 0
        skipped = 0
        for req_obj in queryset:
            # try to resolve the identifier to an existing Student
            student = None
            identifier = req_obj.child_identifier.strip()
            try:
                student = Student.objects.filter(student_id__iexact=identifier).first()
                if not student:
                    student = Student.objects.filter(user__email__iexact=identifier).first()
                if not student:
                    student = Student.objects.filter(user__username__iexact=identifier).first()
            except Exception:
                student = None

            if student:
                # create StudentParent link if not exists
                try:
                    StudentParent.objects.get(parent=req_obj.parent, student=student.user)
                except StudentParent.DoesNotExist:
                    StudentParent.objects.create(parent=req_obj.parent, student=student.user, relationship=req_obj.relationship or 'Parent')

                req_obj.status = 'approved'
                req_obj.save()
                # notify parent that their request was approved
                try:
                    parent_email = req_obj.parent.email
                    if parent_email:
                        send_mail(
                            'Your child link request was approved',
                            f"Your request to link '{req_obj.child_identifier}' to your account was approved.",
                            settings.DEFAULT_FROM_EMAIL,
                            [parent_email],
                            fail_silently=True,
                        )
                except Exception:
                    pass
                approved += 1
            else:
                skipped += 1

        self.message_user(request, f"Approved: {approved}. Skipped (not found): {skipped}.", level=messages.INFO)
    approve_requests.short_description = "Approve selected child link requests"

    def decline_requests(self, request, queryset):
        declined = 0
        for req in queryset:
            req.status = 'declined'
            req.save()
            declined += 1
            try:
                parent_email = req.parent.email
                if parent_email:
                    send_mail(
                        'Your child link request was declined',
                        f"Your request to link '{req.child_identifier}' to your account was declined. Please contact administration.",
                        settings.DEFAULT_FROM_EMAIL,
                        [parent_email],
                        fail_silently=True,
                    )
            except Exception:
                pass

        self.message_user(request, f"Declined: {declined} requests.", level=messages.INFO)
    decline_requests.short_description = "Decline selected child link requests"
