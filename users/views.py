from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from course.models import Enrollment, Course


@login_required
def student_profile(request):
    """個人概況頁面 (相容學生與教師)"""
    user = request.user

    # 1. 學生端 Profile 概況
    if hasattr(user, 'student_profile'):
        student = user.student_profile
        enrollments = Enrollment.objects.filter(student=student).select_related('course')
        total_credits = sum(e.course.credits for e in enrollments)

        context = {
            'role': 'student',
            'student': student,
            'enrollments': enrollments,
            'total_credits': total_credits,
            'credit_percentage': min(round((total_credits / student.max_credits) * 100), 100),
        }
        return render(request, 'student_profile.html', context)

    # 2. 教師端 Profile 概況
    elif hasattr(user, 'teacher_profile'):
        teacher = user.teacher_profile
        courses = Course.objects.filter(teacher=teacher)
        total_students = Enrollment.objects.filter(course__teacher=teacher).count()

        context = {
            'role': 'teacher',
            'teacher': teacher,
            'courses': courses,
            'total_courses': courses.count(),
            'total_students': total_students,
        }
        return render(request, 'student_profile.html', context)

    messages.error(request, "未找到有效的個人檔案資料。")
    return redirect('courses:course_list')