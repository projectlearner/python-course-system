# course/utils.py

def check_student_enrollment_permission(student, course, current_phase):
    """
    檢查學生是否有資格加選該課程
    傳回值：(can_enroll: bool, reason: str)
    """
    student_dept = student.department
    course_dept = course.department
    is_same_dept = (student_dept == course_dept)

    # 1. 通識課程邏輯
    if course.category == 'GENERAL':
        if current_phase == 1:
            return False, "通識課程需至第二階段才開放選修"
        return True, "可選修"

    # 2. 專業課程（本系 vs 外系）
    if is_same_dept:
        # 本系學生：一、二、三階段皆可選（包含專業必修與專業選修）
        return True, "可選修"
    else:
        # 外系學生
        # 漏洞補強：外系專業必修永遠禁止
        if course.type == 'REQUIRED':
            return False, "非本系學生不可選修外系專業必修"

        # 外系專業選修：僅限第三階段
        if course.type == 'ELECTIVE':
            if current_phase < 3:
                return False, "外系專業選修需至第三階段才開放選修"
            return True, "可選修"

    return False, "不符合選修資格"