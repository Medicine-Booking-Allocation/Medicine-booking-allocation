/*
 * Shared domain constants. Roles must match the backend (app/models.py +
 * app/auth_utils.py role_required): 'Customer', 'Pharmacy Staff', 'Administrator'.
 */

export const ROLES = {
  CUSTOMER: 'Customer',
  STAFF: 'Pharmacy Staff',
  ADMIN: 'Administrator',
}

export const ALL_ROLES = [ROLES.CUSTOMER, ROLES.STAFF, ROLES.ADMIN]

/* Where each role lands after login / on a role redirect. */
export const ROLE_DASHBOARD = {
  Customer: '/customer',
  'Pharmacy Staff': '/staff',
  Administrator: '/admin',
}

export function dashboardPathForRole(role) {
  return ROLE_DASHBOARD[role] || '/'
}
