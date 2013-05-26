# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Contains db access functions for users, groups, permissions and courses """

from oasis.lib.DB import run_sql, MC

PERMS = {'OASIS_SUPERUSER': 1, 'OASIS_USERADMIN': 2,
         'OASIS_COURSEADMIN': 3, 'OASIS_COURSECOORD': 4,
         'OASIS_QUESTIONEDITOR': 5, 'OASIS_VIEWMARKS': 8,
         'OASIS_ALTERMARKS': 9, 'OASIS_PREVIEWQUESTIONS': 10,
         'OASIS_PREVIEWASSESSMENT': 11, 'OASIS_CREATEASSESSMENT': 14,
         'OASIS_COURSEMEMBERVIEW': 15, 'OASIS_PREVIEWSURVEY': 16,
         'OASIS_CREATESURVEY': 17, 'OASIS_SYSMESG': 18,
         'OASIS_SYSCOURSES': 19, 'OASIS_SURVEYRESULTS': 20}


def check_perm(user_id, group_id, perm):
    """ Check to see if the user has the permission on the given course. """
    permission = 0
    if not isinstance(perm, int):  # we have a string name so look it up
        if PERMS.has_key(perm):
            permission = PERMS[perm]
    key = "permission-%s-super" % user_id
    obj = MC.get(key)
    if obj:
        return True
        # If they're superuser, let em do anything
    ret = run_sql("""SELECT "id" FROM permissions WHERE userid=%s AND permission=1;""", (user_id,))
    if ret:
        MC.set(key, True)
        return True
        # If we're asking for course -1 it means any course will do.
    if group_id == -1:
        ret = run_sql("""SELECT "id" FROM permissions WHERE userid=%s AND permission=%s;""", (user_id, permission))
        if ret:
            return True
        # Do they have the permission explicitly?
    ret = run_sql("""SELECT "id" FROM permissions WHERE course=%s AND userid=%s AND permission=%s;""",
                  (group_id, user_id, permission))
    if ret:
        return True
        # Now check for global override
    ret = run_sql("""SELECT "id" FROM permissions WHERE course=%s AND userid=%s AND permission='0';""",
                  (group_id, user_id))
    if ret:
        return True
    return False


def satisfyPerms(uid, group_id, permlist):
    """ Does the user have one or more of the permissions in permlist,
        on the given group?
    """
    for perm in permlist:
        if check_perm(uid, group_id, perm):
            return True
    return False


def deletePerm(uid, group_id, perm):
    """Remove a permission. """
    key = "permission-%s-super" % (uid,)
    MC.delete(key)
    run_sql("""DELETE FROM permissions
                WHERE userid=%s AND course=%s AND permission=%s""",
            (uid, group_id, perm))


def addPerm(uid, group_id, perm):
    """ Assign a permission."""
    key = "permission-%s-super" % (uid,)
    MC.delete(key)
    run_sql("""INSERT INTO permissions (course, userid, permission)
             VALUES (%s, %s, %s) """, (group_id, uid, perm))


def getCoursePerms(course_id):
    """ Return a list of all users with permissions on the given course.
        Exclude those who get them via superuser.
    """
    ret = run_sql("""SELECT "id", userid, permission FROM permissions WHERE course=%s;""", (course_id,))
    if not ret:
        return []
    res = [(int(perm[1]), int(perm[2])) for perm in ret if
           perm[2] in [2, 5, 10, 14, 11, 17, 16, 8, 9, 15]]
    # TODO: Magic numbers! get rid of them!
    return res