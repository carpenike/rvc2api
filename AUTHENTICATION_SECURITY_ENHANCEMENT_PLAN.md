# Authentication Security Enhancement Plan

> **Based on Deep Analysis by Gemini AI - January 2025**

This document outlines critical security improvements for the CoachIQ authentication system based on comprehensive analysis of the current implementation and RV-specific threat modeling.

## 🏗️ **Architecture Principle: Backend-Only Business Logic**

**CRITICAL**: All authentication business logic, security decisions, and state management MUST remain in the backend. The frontend serves only as a presentation layer that consumes backend APIs and handles user interactions.

### **Frontend Responsibilities (Presentation Only)**
- Display authentication UI components using **shadcn/ui design system**
- Handle user input and form validation (client-side convenience only)
- Store and send JWT tokens in requests
- Handle token refresh mechanics (call backend endpoints)
- Display authentication status and error messages
- Update existing sidenav user component to use auth state from backend

### **Backend Responsibilities (All Business Logic)**
- Authentication mode detection and enforcement
- Password generation, validation, and hashing
- JWT token creation, validation, and expiration logic
- Session management and refresh token handling
- Rate limiting enforcement and configuration
- Security policy enforcement (password strength, device fingerprinting)
- All authentication state persistence (database or in-memory)
- Authentication flow orchestration and business rules

## 📊 Current Authentication Modes

The system currently supports three authentication modes with specific use cases:

### **1. NONE Mode (No Authentication)**
- **When Used**: `COACHIQ_AUTH__ENABLED=false` or no auth config
- **Behavior**: All requests allowed, mock admin user returned
- **Use Cases**: Development, testing, trusted environments
- **Security Impact**: ⚠️ No protection - appropriate for isolated systems only

### **2. SINGLE_USER Mode**
- **When Used**: `COACHIQ_AUTH__ENABLED=true` + username/password provided + magic links disabled
- **Environment Variables**:
  ```bash
  COACHIQ_AUTH__ENABLED=true
  COACHIQ_AUTH__ADMIN_USERNAME=admin
  COACHIQ_AUTH__ADMIN_PASSWORD=mypassword  # Auto-generated if empty
  COACHIQ_AUTH__ENABLE_MAGIC_LINKS=false
  ```
- **Behavior**:
  - Auto-generates secure password if not provided
  - Works without persistence (in-memory only)
  - Forces password change on first login (if auto-generated)
  - Uses bcrypt hashing when available, falls back to plaintext

### **3. MULTI_USER Mode**
- **When Used**: `COACHIQ_AUTH__ENABLED=true` + magic links or OAuth enabled
- **Environment Variables**:
  ```bash
  COACHIQ_AUTH__ENABLED=true
  COACHIQ_AUTH__ADMIN_EMAIL=admin@example.com
  COACHIQ_AUTH__ENABLE_MAGIC_LINKS=true
  ```
- **Behavior**:
  - Supports magic link authentication
  - Requires notification system for email sending
  - Full user management with database persistence
  - Invitation-based user registration

## 🚨 Critical Issues Identified

### 1. **Mode Auto-Detection Security Risk** ⚠️ **PARTIALLY MITIGATED**
- **Current State**: Auto-detection logic is deterministic and well-defined
- **Remaining Issue**: No protection against environment variable manipulation
- **Risk**: Configuration changes could alter security posture unexpectedly
- **Impact**: Medium - Risk exists but current logic is robust

### 2. **JWT Strategy Usability Problems**
- **Issue**: 30-minute JWT expiry forces constant re-authentication via magic links
- **Current Workaround**: Single-user mode doesn't suffer from this (no magic links)
- **Impact**: High - Affects multi-user mode usability significantly

### 3. **RV-Specific Security Threats**
- **Physical Access**: JWT secret keys vulnerable in plaintext storage
- **Offline Lockout**: Multi-user mode affected, single-user mode works offline
- **Shared Devices**: Family tablets with email access create attack vectors
- **Impact**: Critical - Unique to RV deployment environment

### 4. **Password Management Inconsistencies**
- **Issue**: Auto-generated passwords logged in plaintext to console
- **Risk**: Sensitive credentials exposed in log files
- **Impact**: High - Security best practice violation

### 5. **Persistence Assumptions**
- **Issue**: Some enhancements assume database availability
- **Reality**: System must work with persistence disabled
- **Impact**: Medium - Limits enhancement applicability

## 🎨 **Shadcn/UI Integration Requirements**

### **Install Required shadcn Components**
```bash
cd frontend
npx shadcn@latest add login-01  # Login form template
```

### **Existing shadcn Components Available**
✅ **Already Installed:**
- Card, Button, Input, Label, Form (login components)
- Avatar, DropdownMenu (nav-user components)
- Table, Dialog, Alert, Badge, Progress
- Skeleton, Separator, Tabs, Switch

### **Nav-User Component Integration**
The existing `nav-user.tsx` component needs to be updated to:

1. **Replace static user data** with auth context from backend APIs
2. **Handle authentication states**: logged in, logged out, loading
3. **Show different menus** based on authentication mode (none/single/multi-user)
4. **Add logout functionality** that calls backend logout endpoint
5. **Display user role** and authentication status indicators

### **Component Integration Plan**
- `app-sidebar.tsx` → Update user data source from auth context
- `nav-user.tsx` → Integrate with auth state, maintain shadcn design
- `login-form.tsx` → Update to use auth context and backend APIs
- **New components** → All built with shadcn components exclusively

### **Complete Frontend Component List**

**📝 Components to Modify:**
- `components/nav-user.tsx` → Auth context integration
- `components/app-sidebar.tsx` → User data from auth context
- `components/login-form.tsx` → Backend API integration

**🆕 New Components to Create:**
- `components/admin-credentials.tsx` → Auto-generated password display (Card, Alert)
- `components/setup-wizard.tsx` → Multi-user setup (Form, Card, Progress)
- `components/rate-limit-indicator.tsx` → Rate limit status (Alert, Badge)
- `components/device-alert.tsx` → New device notifications (Alert)
- `pages/device-management.tsx` → Device management (Table, Dialog, Badge)
- `pages/api-keys.tsx` → API key management (Table, Form, Chart)
- `pages/audit-logs.tsx` → Security audit logs (Table, Badge)
- `components/api-key-form.tsx` → API key creation (Form, Input, Dialog)

**🔧 Contexts & Hooks:**
- `contexts/auth-context.tsx` → Authentication state management
- `hooks/useOfflineAuth.ts` → Offline authentication status
- `utils/deviceFingerprint.ts` → Device fingerprint collection

## 📋 Implementation Plan

### **Phase 1: Critical Security Fixes (Week 1-2)**
> **Priority**: 🔴 Critical - Security vulnerabilities

#### 1.1 Password Security Hardening
- [ ] **Backend**: Remove plaintext password logging from console output
- [ ] **Backend**: Implement secure credential display mechanism (one-time display API)
- [ ] **Backend**: Add password strength validation for user-provided passwords
- [ ] **Backend**: Ensure bcrypt is always available (add to required dependencies)
- [ ] **Backend**: Add secure password change flow for auto-generated credentials
- [ ] **Backend**: Create `/api/auth/admin/credentials` endpoint for one-time credential retrieval
- [ ] **Frontend**: Install shadcn login components: `npx shadcn@latest add login-01`
- [ ] **Frontend**: Create admin credentials display component using shadcn Card/Alert
- [ ] **Frontend**: Update existing `nav-user.tsx` to integrate with auth context

**Files to modify:**
- `backend/services/auth_manager.py` (credential logic)
- `backend/core/config.py` (password policies)
- `backend/api/routers/auth.py` (credential display endpoint)
- `pyproject.toml` (ensure bcrypt/passlib required)
- `frontend/src/components/admin-credentials.tsx` (new, shadcn components)
- `frontend/src/components/nav-user.tsx` (update to use auth state)

#### 1.2 System Initialization Enhancement (Multi-User Only)
- [ ] **Backend**: Add optional explicit setup flow for multi-user mode
- [ ] **Backend**: Preserve existing environment variable configuration
- [ ] **Backend**: Add `/api/auth/setup/status` endpoint to check initialization state
- [ ] **Backend**: Add `/api/auth/setup/initialize` endpoint for setup completion
- [ ] **Backend**: Implement setup wizard business logic and validation
- [ ] **Frontend**: Build setup wizard using shadcn Form, Card, Button, Input components
- [ ] **Frontend**: Use shadcn Step/Progress components for multi-step setup
- [ ] **Backend**: Maintain backward compatibility with current modes

**Applies to:** Multi-user mode only (single-user and none modes unchanged)

**shadcn Components Needed:**
- Form, Card, Button, Input (already available)
- Progress, Separator (already available)
- Alert for status messages

**Files to modify:**
- `backend/services/auth_manager.py` (setup logic)
- `backend/api/routers/auth.py` (setup endpoints)
- `backend/models/auth.py` (setup state tracking)
- `frontend/src/components/setup-wizard.tsx` (shadcn UI components only)

#### 1.3 Rate Limiting Implementation
- [ ] **Backend**: Install and configure `slowapi` middleware
- [ ] **Backend**: Add rate limiting to `/auth/magic-link` (5 requests/hour)
- [ ] **Backend**: Add rate limiting to `/auth/verify-link` (10 requests/hour)
- [ ] **Backend**: Add general API rate limiting (100 requests/minute)
- [ ] **Backend**: Bypass rate limiting for single-user and none modes
- [ ] **Backend**: Implement rate limit status headers for frontend feedback
- [ ] **Frontend**: Display rate limit status using shadcn Alert/Badge components

**Applies to:** All modes (with mode-specific configurations)

**shadcn Components Needed:**
- Alert, Badge (already available via existing components)

**Files to modify:**
- `backend/middleware/http.py` (rate limiting logic)
- `pyproject.toml` (add slowapi dependency)
- `frontend/src/components/rate-limit-indicator.tsx` (shadcn Alert/Badge display)

#### 1.4 Secure Secret Storage
- [ ] **Backend**: Implement encrypted storage for JWT secrets
- [ ] **Backend**: Add environment variable for decryption key
- [ ] **Backend**: Update configuration loading to decrypt secrets
- [ ] **Backend**: Document key management procedures
- [ ] **Backend**: Ensure compatibility with persistence-disabled scenarios
- [ ] **Backend**: Create secret rotation mechanism

**Applies to:** All modes that use JWT tokens (single-user and multi-user)

**Files to modify:**
- `backend/core/config.py` (encryption/decryption logic)
- `backend/services/auth_manager.py` (secret handling)

### **Phase 2: Refresh Token Implementation (Week 3-4)**
> **Priority**: 🟡 High - Usability critical for multi-user mode

**Applies to:** Multi-user mode only (single-user mode uses longer JWT lifetimes)

#### 2.1 Database Schema Updates
- [ ] **Backend**: Add refresh token fields to `UserSession` model
- [ ] **Backend**: Create migration for new fields
- [ ] **Backend**: Add refresh token hashing utilities
- [ ] **Backend**: Add in-memory fallback for persistence-disabled scenarios

**Files to modify:**
- `backend/models/auth.py` (schema updates)
- `alembic/versions/` (new migration)
- `backend/services/in_memory_persistence.py` (in-memory storage)

#### 2.2 Refresh Token Backend Logic
- [ ] **Backend**: Implement refresh token generation and storage logic
- [ ] **Backend**: Create `/api/auth/refresh` endpoint
- [ ] **Backend**: Update magic link flow to return refresh tokens
- [ ] **Backend**: Add HttpOnly cookie handling for refresh tokens
- [ ] **Backend**: Implement token rotation on refresh
- [ ] **Backend**: Add persistence-aware storage (database vs in-memory)
- [ ] **Backend**: Implement refresh token expiration and cleanup

**Files to modify:**
- `backend/services/auth_manager.py` (token business logic)
- `backend/api/routers/auth.py` (refresh endpoint)
- `backend/middleware/auth.py` (cookie handling)

#### 2.3 Frontend Token Management & UI Updates
- [ ] **Frontend**: Update API client to call refresh endpoint
- [ ] **Frontend**: Implement automatic retry on 401 responses
- [ ] **Frontend**: Add token refresh interceptor (calls backend only)
- [ ] **Frontend**: Update logout to call backend logout endpoint
- [ ] **Frontend**: Update existing `login-form.tsx` to use auth context and proper form handling
- [ ] **Frontend**: Create mode-aware login components (single-user vs multi-user)
- [ ] **Frontend**: Update `nav-user.tsx` to show authenticated user state
- [ ] **Frontend**: Add authentication loading states using shadcn Skeleton components

**shadcn Components Used:**
- Existing: Form, Input, Button, Card (login-form.tsx)
- Skeleton for loading states
- Badge for authentication mode indication

**Files to modify:**
- `frontend/src/api/client.ts` (HTTP client logic)
- `frontend/src/contexts/auth-context.tsx` (UI state management)
- `frontend/src/components/login-form.tsx` (update to use auth context)
- `frontend/src/components/nav-user.tsx` (integrate auth state)
- `frontend/src/components/app-sidebar.tsx` (update user data source)

#### 2.4 Nav-User Component Integration
- [ ] **Frontend**: Install shadcn login-01 template: `cd frontend && npx shadcn@latest add login-01`
- [ ] **Frontend**: Create auth context with user state management
- [ ] **Frontend**: Update `nav-user.tsx` to consume auth context instead of static data
- [ ] **Frontend**: Add authentication mode indicator (Badge) to nav-user
- [ ] **Frontend**: Update nav-user dropdown menu items based on auth state
- [ ] **Frontend**: Add proper logout functionality that calls backend `/api/auth/logout`
- [ ] **Frontend**: Update `app-sidebar.tsx` to get user data from auth context
- [ ] **Frontend**: Add loading states for user data using Skeleton components
- [ ] **Frontend**: Handle unauthenticated state (redirect to login or show login button)

**Nav-User Component States:**
- **NONE Mode**: Show static "No Auth" indicator
- **SINGLE_USER Mode**: Show admin user with logout option
- **MULTI_USER Mode**: Show authenticated user with full menu options
- **Loading**: Show skeleton placeholder
- **Unauthenticated**: Show login button/redirect

**Files to modify:**
- `frontend/src/components/nav-user.tsx` (integrate with auth context)
- `frontend/src/components/app-sidebar.tsx` (use auth context for user data)
- `frontend/src/contexts/auth-context.tsx` (user state management)
- `frontend/src/api/endpoints.ts` (auth API calls)

### **Phase 3: RV-Specific Adaptations (Week 5-6)**
> **Priority**: 🟢 Medium - Environment-specific

#### 3.1 Mode-Specific Offline Authentication
- [ ] **Backend**: Extend JWT lifetime to 24-72 hours for single-user mode
- [ ] **Backend**: Implement graceful degradation with cached sessions for multi-user mode
- [ ] **Backend**: Add offline-aware token validation logic
- [ ] **Backend**: Create mode-aware credential caching policies
- [ ] **Backend**: Add `/api/auth/offline-status` endpoint for connectivity awareness
- [ ] **Frontend**: Display offline authentication status (no logic, calls backend)

**Mode Applicability:**
- **Single-User**: Long-lived tokens, reduced security for convenience
- **Multi-User**: Cached refresh tokens with expiration warnings
- **None**: No authentication changes

**Files to modify:**
- `backend/core/config.py` (offline configuration)
- `backend/services/auth_manager.py` (offline logic)
- `backend/api/routers/auth.py` (offline status endpoint)
- `frontend/src/hooks/useOfflineAuth.ts` (display logic only)

#### 3.2 Device Fingerprinting for Magic Links
- [ ] **Backend**: Add device fingerprint capture on magic link request
- [ ] **Backend**: Compare fingerprints on magic link verification
- [ ] **Backend**: Implement "new device" notifications logic
- [ ] **Backend**: Add device management endpoints for users
- [ ] **Backend**: Store device information in database/memory
- [ ] **Frontend**: Collect device fingerprint data and send to backend
- [ ] **Frontend**: Create device management page using shadcn Table, Badge, Dialog components
- [ ] **Frontend**: Add "new device" notification using shadcn Alert components

**Applies to:** Multi-user mode only (magic links not used in single-user mode)

**shadcn Components Used:**
- Table for device listing
- Badge for device status
- Dialog for device management actions
- Alert for new device notifications

**Files to modify:**
- `backend/services/auth_manager.py` (fingerprinting logic)
- `backend/models/auth.py` (device storage)
- `backend/api/routers/auth.py` (device management endpoints)
- `frontend/src/utils/deviceFingerprint.ts` (data collection only)
- `frontend/src/pages/device-management.tsx` (new, shadcn components)
- `frontend/src/components/device-alert.tsx` (new device notifications)

### **Phase 4: Advanced Security Features (Week 7-8)**
> **Priority**: 🔵 Low - Enhanced security

#### 4.1 CSRF Protection
- [ ] **Backend**: Implement CSRF middleware for cookie-based endpoints
- [ ] **Backend**: Add CSRF token generation and validation
- [ ] **Backend**: Add CSRF tokens to refresh token flow
- [ ] **Frontend**: Include CSRF tokens in requests (token retrieval from backend)

**Files to modify:**
- `backend/middleware/http.py` (CSRF logic)
- `backend/api/routers/auth.py` (CSRF token endpoint)
- `frontend/src/api/client.ts` (token inclusion)

#### 4.2 Enhanced Audit Logging
- [ ] **Backend**: Implement tamper-resistant audit logs
- [ ] **Backend**: Add external log shipping for multi-user mode
- [ ] **Backend**: Add security event monitoring and alerting
- [ ] **Backend**: Create audit log API endpoints
- [ ] **Frontend**: Create audit log viewer for admins (display only)

**Files to modify:**
- `backend/services/auth_manager.py` (audit logic)
- `backend/models/auth.py` (audit schema)
- `backend/api/routers/auth.py` (audit endpoints)
- `frontend/src/pages/audit-logs.tsx` (display only)

#### 4.3 API Key Security Hardening
- [ ] **Backend**: Hash API key secrets (don't store plaintext)
- [ ] **Backend**: Add API key prefixes for identification
- [ ] **Backend**: Implement API key rotation logic
- [ ] **Backend**: Add usage analytics and alerts
- [ ] **Backend**: Create API key management endpoints
- [ ] **Frontend**: Create API key management page using shadcn Table, Dialog, Input components
- [ ] **Frontend**: Add API key creation form using shadcn Form components
- [ ] **Frontend**: Display usage analytics using shadcn Chart components

**shadcn Components Used:**
- Table for API key listing
- Dialog for key creation/deletion
- Form, Input for key details
- Badge for key status
- Chart for usage analytics

**Files to modify:**
- `backend/models/auth.py` (API key schema)
- `backend/services/auth_manager.py` (API key logic)
- `backend/api/routers/auth.py` (API key endpoints)
- `frontend/src/pages/api-keys.tsx` (shadcn components)
- `frontend/src/components/api-key-form.tsx` (new, key creation)

### **Phase 5: Testing and Validation (Week 9-10)**
> **Priority**: 🟡 High - Quality assurance

#### 5.1 Backend Security Testing Suite
- [ ] **Backend**: State transition testing (setup scenarios)
- [ ] **Backend**: Token expiry and refresh testing
- [ ] **Backend**: Rate limiting validation
- [ ] **Backend**: Offline simulation testing
- [ ] **Backend**: Physical access simulation
- [ ] **Backend**: Mode detection and switching tests

**Files to create:**
- `tests/security/test_auth_state_transitions.py`
- `tests/security/test_token_management.py`
- `tests/security/test_rate_limiting.py`
- `tests/security/test_offline_scenarios.py`
- `tests/security/test_mode_detection.py`

#### 5.2 Integration Testing
- [ ] **Backend**: End-to-end authentication flow APIs
- [ ] **Backend**: WebSocket authentication testing
- [ ] **Backend**: Multi-device session testing
- [ ] **Backend**: Cross-mode functionality testing
- [ ] **Frontend**: UI integration tests (API consumption only)
- [ ] **Frontend**: Authentication state management testing

**Files to create/modify:**
- `tests/integrations/auth/test_complete_flows.py`
- `tests/integrations/auth/test_cross_mode.py`
- `frontend/src/test/auth-integration.test.tsx` (UI state only)

## 🔧 Configuration Updates Required

### Feature Flags (`backend/services/feature_flags.yaml`)
```yaml
authentication:
  enabled: true
  mode: "auto"  # Preserve existing auto-detection
  require_setup: false  # Optional setup wizard for multi-user
  refresh_token_enabled: true
  offline_mode_enabled: true
  rate_limiting_enabled: true
  password_security_enhanced: true
```

### Environment Variables (`.env.example`)
```bash
# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# Basic Authentication Control
COACHIQ_AUTH__ENABLED=true
COACHIQ_AUTH__MODE=auto  # auto, none, single-user, multi-user

# Single-User Mode Configuration
COACHIQ_AUTH__ADMIN_USERNAME=admin
COACHIQ_AUTH__ADMIN_PASSWORD=  # Auto-generated if empty
COACHIQ_AUTH__ENABLE_MAGIC_LINKS=false  # Disable for single-user

# Multi-User Mode Configuration
COACHIQ_AUTH__ADMIN_EMAIL=admin@example.com
COACHIQ_AUTH__ENABLE_MAGIC_LINKS=true
COACHIQ_AUTH__ENABLE_OAUTH=false

# Security Enhancements
COACHIQ_AUTH__SECRET_ENCRYPTION_KEY=<32-char-key>
COACHIQ_AUTH__REFRESH_TOKEN_DAYS=30
COACHIQ_AUTH__SINGLE_USER_JWT_HOURS=72  # Extended for offline scenarios
COACHIQ_AUTH__MULTI_USER_JWT_MINUTES=15  # Short-lived with refresh tokens
COACHIQ_AUTH__RATE_LIMIT_ENABLED=true

# JWT Configuration
COACHIQ_AUTH__SECRET_KEY=  # Auto-generated if empty
COACHIQ_AUTH__JWT_EXPIRE_MINUTES=30  # Default, overridden by mode-specific settings
COACHIQ_AUTH__MAGIC_LINK_EXPIRE_MINUTES=15
```

### Mode-Specific Behavior Matrix

| Setting | NONE Mode | SINGLE_USER Mode | MULTI_USER Mode |
|---------|-----------|------------------|-----------------|
| **Authentication Required** | ❌ No | ✅ Yes | ✅ Yes |
| **JWT Tokens** | ❌ No | ✅ Yes (long-lived) | ✅ Yes (short-lived) |
| **Refresh Tokens** | ❌ No | ❌ No | ✅ Yes |
| **Magic Links** | ❌ No | ❌ No | ✅ Yes |
| **Database Required** | ❌ No | ❌ No | ⚠️ Optional |
| **Rate Limiting** | ⚠️ Light | ⚠️ Light | ✅ Full |
| **Offline Support** | ✅ Full | ✅ Full | ⚠️ Limited |
| **Setup Wizard** | ❌ No | ❌ No | ⚠️ Optional |

## 📊 Risk Assessment

| Phase | Risk Level | Impact | Effort | Priority |
|-------|------------|---------|--------|----------|
| Phase 1 | Critical | High | Medium | 🔴 Immediate |
| Phase 2 | High | High | High | 🟡 Next Sprint |
| Phase 3 | Medium | Medium | Medium | 🟢 Following Sprint |
| Phase 4 | Low | Low | High | 🔵 Future |
| Phase 5 | Medium | High | Medium | 🟡 Parallel |

## 🎯 Success Criteria

### Phase 1 Complete
- [ ] No auto-detection vulnerabilities remain
- [ ] All auth endpoints are rate-limited
- [ ] JWT secrets are encrypted at rest
- [ ] Setup wizard prevents unauthorized access

### Phase 2 Complete
- [ ] Users can stay logged in for reasonable periods
- [ ] Token refresh works seamlessly
- [ ] No more magic link fatigue

### Phase 3 Complete
- [ ] System works reliably offline (single-user)
- [ ] Multi-user gracefully handles connectivity loss
- [ ] Device security is enhanced

### Phases 4-5 Complete
- [ ] Comprehensive security test coverage
- [ ] All security best practices implemented
- [ ] System is production-ready for all scenarios

## 📝 Implementation Notes

### Dependencies to Add
```toml
# pyproject.toml additions
slowapi = "^0.1.9"  # Rate limiting
cryptography = "^41.0.0"  # Secret encryption
```

### Breaking Changes
- **Password Logging**: Auto-generated passwords will no longer appear in logs (security improvement)
- **Token Lifetimes**: Different JWT expiry times based on authentication mode
- **Refresh Tokens**: New cookie-based refresh flow for multi-user mode
- **Rate Limiting**: New limits on authentication endpoints

### Migration Strategy
1. **Phase 1**: Deploy security fixes with backward compatibility
2. **Phase 2**: Add refresh token schema with graceful fallback
3. **Phase 3**: Update mode-specific token lifetimes
4. **Phase 4+**: Optional advanced features as needed

### Backward Compatibility
- **Existing environment variables**: All current variables continue to work
- **Authentication modes**: Current mode detection logic preserved
- **API endpoints**: No breaking changes to existing auth endpoints
- **Database schema**: Additive changes only, no destructive migrations

---

**Last Updated**: January 2025
**Review Date**: After each phase completion
**Stakeholders**: Security team, DevOps, Product owner
