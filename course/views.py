from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Course, Enrollment, CourseTime, DEPARTMENT_CHOICES, CATEGORY_CHOICES

# 目前選課階段
CURRENT_PHASE = 2


def check_course_permission(student, course, current_phase):
    """統一選課權限檢查 Helper"""
    if not student:
        return False, "請先登入學生帳號"

    is_same_dept = (student.department == course.department)

    # 1. 外系專業必修：任何階段皆全面禁止
    if course.category == 'REQUIRED' and not is_same_dept:
        return False, f"限 {course.get_department_display()} 學生"

    # 2. 通識課程
    if course.category == 'GENERAL':
        if current_phase < 2:
            return False, "通識課程需至第二階段才開放選修"
        return True, ""

    # 3. 本系課程（必修 / 選修）
    if is_same_dept:
        return True, ""

    # 4. 外系專業選修
    if course.category == 'ELECTIVE' and not is_same_dept:
        if current_phase < 3:
            return False, "跨系課程 (暫未開放)"
        return True, ""

    return False, "不符合選修條件"


def course_list(request):
    """課程清單 & QuerySet Chaining 複合搜尋"""
    selected_dept = request.GET.get('dept', '')
    selected_category = request.GET.get('category', '')
    search_query = request.GET.get('q', '').strip()

    courses = Course.objects.select_related('teacher').all()

    # 鏈式篩選
    if selected_dept:
        courses = courses.filter(department=selected_dept)
    if selected_category:
        courses = courses.filter(category=selected_category)
    if search_query:
        courses = courses.filter(title__icontains=search_query)

    student_profile = getattr(request.user, 'student_profile', None)
    is_teacher = hasattr(request.user, 'teacher_profile')

    enrolled_course_ids = set()
    if student_profile:
        enrolled_course_ids = set(
            Enrollment.objects.filter(student=student_profile).values_list('course_id', flat=True)
        )

    current_phase = CURRENT_PHASE
    course_data = []

    for course in courses:
        is_enrolled = course.id in enrolled_course_ids

        if is_teacher:
            can_enroll = False
            disabled_reason = "教師身份無法選課"
        elif is_enrolled:
            can_enroll = False
            disabled_reason = "已在課表中"
        else:
            can_enroll, disabled_reason = check_course_permission(
                student_profile, course, current_phase
            )

        course_data.append({
            'course': course,
            'can_enroll': can_enroll,
            'is_enrolled': is_enrolled,
            'disabled_reason': disabled_reason,
        })

    context = {
        'course_data': course_data,
        'department_choices': DEPARTMENT_CHOICES,
        'category_choices': CATEGORY_CHOICES,
        'selected_dept': selected_dept,
        'selected_category': selected_category,
        'search_query': search_query,
        'current_phase': current_phase,
        'is_teacher': is_teacher,
    }
    return render(request, 'courses/course_list.html', context)


def course_detail(request, course_id):
    """課程詳情"""
    course = get_object_or_404(Course.objects.prefetch_related('times'), id=course_id)

    is_enrolled = False
    can_enroll = False
    disabled_reason = ""
    current_phase = CURRENT_PHASE
    is_teacher = hasattr(request.user, 'teacher_profile')

    if request.user.is_authenticated:
        if is_teacher:
            can_enroll = False
            disabled_reason = "教師身份無法選課"
        elif hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
            is_enrolled = Enrollment.objects.filter(student=student, course=course).exists()

            if is_enrolled:
                disabled_reason = "你已選修此課程"
            else:
                can_enroll, disabled_reason = check_course_permission(student, course, current_phase)

    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'can_enroll': can_enroll,
        'disabled_reason': disabled_reason,
        'current_phase': current_phase,
        'is_teacher': is_teacher,
    }
    return render(request, 'courses/course_detail.html', context)


@transaction.atomic
@login_required
def enroll_course(request, course_id):
    """加選課程邏輯"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        current_phase = CURRENT_PHASE

        if not hasattr(request.user, 'student_profile'):
            messages.error(request, '只有學生身份可以進行選課！')
            return redirect('courses:course_detail', course_id=course.id)

        student = request.user.student_profile

        # 1. 檢查學分上限
        current_enrollments = Enrollment.objects.filter(student=student)
        current_credits = sum(e.course.credits for e in current_enrollments)

        if current_credits + course.credits > student.max_credits:
            messages.error(request, f"加選失敗：超過單學期學分上限（目前 {current_credits} + 本課 {course.credits} > 上限 {student.max_credits}）！")
            return redirect('courses:course_list')

        # 2. 檢查選課階段與權限
        can_enroll, disabled_reason = check_course_permission(student, course, current_phase)
        if not can_enroll:
            messages.error(request, f'選課失敗：{disabled_reason}！')
            return redirect('courses:course_detail', course_id=course.id)

        # 3. 檢查重複選課
        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.warning(request, '你已經選過這門課程了。')
            return redirect('courses:course_detail', course_id=course.id)

        # 4. 檢查課表衝堂
        enrolled_course_ids = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
        student_enrolled_times = set(
            CourseTime.objects.filter(course_id__in=enrolled_course_ids).values_list('weekday', 'period')
        )
        new_course_times = set(course.times.values_list('weekday', 'period'))

        overlapping_times = student_enrolled_times.intersection(new_course_times)
        if overlapping_times:
            conflict_msg = ", ".join([f"週{w}第{p}節" for w, p in sorted(overlapping_times)])
            messages.error(request, f'選課失敗：與已選課程時間衝堂（{conflict_msg}）！')
            return redirect('courses:course_detail', course_id=course.id)

        # 5. 名額限制與悲觀鎖
        with transaction.atomic():
            course_obj = Course.objects.select_for_update().get(id=course_id)
            current_enrolled = Enrollment.objects.filter(course=course_obj).count()

            if hasattr(course_obj, 'capacity') and current_enrolled >= course_obj.capacity:
                messages.error(request, '選課失敗：該課程名額已滿！')
                return redirect('courses:course_detail', course_id=course.id)

            Enrollment.objects.create(student=student, course=course_obj)
            messages.success(request, f'成功加選課程：{course_obj.title}！')

        return redirect('courses:my_courses')

    return redirect('courses:course_list')


@login_required
def my_courses(request):
    """個人課表/已選課程列表"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, '請先完善學生資料。')
        return redirect('courses:course_list')

    student = request.user.student_profile
    enrollments = Enrollment.objects.filter(student=student).select_related('course').prefetch_related('course__times')

    timetable_matrix = {day: {period: [] for period in range(1, 11)} for day in range(1, 8)}

    for enrollment in enrollments:
        for time_slot in enrollment.course.times.all():
            if 1 <= time_slot.weekday <= 7 and 1 <= time_slot.period <= 10:
                timetable_matrix[time_slot.weekday][time_slot.period].append(time_slot)

    PERIOD_TIMES = {
        1: '08:10 - 09:00',
        2: '09:10 - 10:00',
        3: '10:10 - 11:00',
        4: '11:10 - 12:00',
        5: '13:30 - 14:20',
        6: '14:25 - 15:15',
        7: '15:25 - 16:15',
        8: '16:20 - 17:10',
        9: '17:15 - 18:05',
        10: '',
    }

    grid = []
    for period in range(1, 11):
        row = []
        for day in range(1, 8):
            row.append(timetable_matrix[day][period])
        grid.append((period, PERIOD_TIMES.get(period, ''), row))

    return render(request, 'courses/my_courses.html', {
        'enrollments': enrollments,
        'grid': grid,
    })


@login_required
def drop_course(request, course_id):
    """退選課程邏輯"""
    if request.method == 'POST':
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, '只有學生身份可以進行退選！')
            return redirect('courses:my_courses')

        student = request.user.student_profile
        course = get_object_or_404(Course, id=course_id)

        enrollment = Enrollment.objects.filter(student=student, course=course).first()
        if enrollment:
            enrollment.delete()
            messages.success(request, f'已成功退選課程：{course.title}！')
        else:
            messages.error(request, '退選失敗：你尚未選修此門課程。')

        return redirect('courses:my_courses')

    return redirect('courses:my_courses')


@login_required
def teacher_courses(request):
    """教師查看授課清單"""
    if not hasattr(request.user, 'teacher_profile'):
        messages.error(request, "您沒有權限存取教師端系統！")
        return redirect('courses:course_list')

    teacher = request.user.teacher_profile
    courses = Course.objects.filter(teacher=teacher)

    return render(request, 'teacher_courses.html', {'courses': courses})


@login_required
def course_roster(request, course_id):
    """教師成績登記頁"""
    if not hasattr(request.user, 'teacher_profile'):
        messages.error(request, "權限不足，您並非教師帳號！")
        return redirect('courses:course_list')

    course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher_profile)
    enrollments = Enrollment.objects.filter(course=course).select_related('student__user')

    if request.method == 'POST':
        for enrollment in enrollments:
            daily = request.POST.get(f'daily_{enrollment.id}')
            midterm = request.POST.get(f'midterm_{enrollment.id}')
            final = request.POST.get(f'final_{enrollment.id}')

            enrollment.daily_score = float(daily) if daily else None
            enrollment.midterm_score = float(midterm) if midterm else None
            enrollment.final_score = float(final) if final else None
            enrollment.save()

        messages.success(request, f"已成功更新【{course.title}】的成績資料！")
        return redirect('courses:course_roster', course_id=course.id)

    context = {
        'course': course,
        'enrollments': enrollments,
    }
    return render(request, 'course_roster.html', context)

@login_required
def edit_course(request, course_id):
    """教師編輯課程資訊"""
    if not hasattr(request.user, 'teacher_profile'):
        messages.error(request, "您沒有權限修改課程資訊！")
        return redirect('courses:course_list')

    course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher_profile)

    if request.method == 'POST':
        course.title = request.POST.get('title', course.title)
        course.classroom = request.POST.get('classroom', course.classroom)
        course.capacity = int(request.POST.get('capacity', course.capacity))
        course.description = request.POST.get('description', course.description)
        course.save()

        messages.success(request, f"已成功更新課程【{course.title}】的資訊！")
        return redirect('courses:teacher_courses')

    return render(request, 'edit_course.html', {'course': course})