from uganda_common.reports import XFormSubmissionColumn, XFormAttributeColumn, PollNumericResultsColumn, PollCategoryResultsColumn, LocationReport

GRADES = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']

class MainEmisReport(LocationReport):
    boys_p3 = XFormAttributeColumn('boys_p3')
    girls_p3 = XFormAttributeColumn('girls_p3')

    boys_p5 = XFormAttributeColumn('boys_p5')
    girls_p5 = XFormAttributeColumn('girls_p5')

    deploy_m = XFormAttributeColumn('deploy_m')
    deploy_f = XFormAttributeColumn('deploy_f')

    gemabuse_cases = XFormAttributeColumn('gemabuse_cases')
    classrooms_p4 = XFormAttributeColumn('classrooms_p5')

class ClassRoomReport(LocationReport):
    classrooms_p1 = XFormAttributeColumn('classrooms_p1')
    classroomsused_p1 = XFormAttributeColumn('classroomsused_p1')

    classrooms_p2 = XFormAttributeColumn('classrooms_p2')
    classroomsused_p2 = XFormAttributeColumn('classroomsused_p2')

    classrooms_p3 = XFormAttributeColumn('classrooms_p3')
    classroomsused_p3 = XFormAttributeColumn('classroomsused_p3')

    classrooms_p4 = XFormAttributeColumn('classrooms_p4')
    classroomsused_p4 = XFormAttributeColumn('classroomsused_p4')

    classrooms_p5 = XFormAttributeColumn('classrooms_p5')
    classroomsused_p5 = XFormAttributeColumn('classroomsused_p5')

    classrooms_p6 = XFormAttributeColumn('classrooms_p6')
    classroomsused_p6 = XFormAttributeColumn('classroomsused_p6')

    classrooms_p7 = XFormAttributeColumn('classrooms_p7')
    classroomsused_p7 = XFormAttributeColumn('classroomsused_p7')

class DashBoardReport(LocationReport):
    pupil_attendance = XFormAttributeColumn((["boys_%s" % g for g in GRADES] + ["girls_%s" % g for g in GRADES]))
    teacher_attendance = XFormAttributeColumn("gemteachers_htpresent")
    total_enrollment = XFormAttributeColumn((["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]))
    teacher_deployment = XFormAttributeColumn(["deploy_m", "deploy_g"])
    abuse = XFormAttributeColumn("gemabuse_cases")
