from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from course.models import Enrollment

@login_required
def student_profile(request):
    # 檢查是否具備學生 Profile
    if not hasattr(request.user, 'student_profile'):
        messages.warning(request, "您目前以教師身份登入，無法存取學生個人主頁。")
        return redirect('courses:teacher_courses') # 自動導向教師端
        
    student = request.user.student_profile
    enrollments = Enrollment.objects.filter(student=student).select_related('course')
    total_credits = sum(e.course.credits for e in enrollments)
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'total_credits': total_credits,
    }
    return render(request, 'student_profile.html', context)