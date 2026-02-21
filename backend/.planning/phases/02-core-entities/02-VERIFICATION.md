---
phase: 02-core-entities
verified: 2026-03-28T00:00:00Z
status: gaps_found
score: 4/5 requirements verified
re_verification: false
gaps:
  - truth: "Shop owner can upload multiple photos during shop setup wizard"
    status: partial
    reason: >
      The frontend ShopSetupPage.vue sends all selected photos in a single POST
      request by appending each file under the same 'image' key in FormData.
      The backend ShopPhotoView.post uses ShopPhotoSerializer which handles a
      single ImageField — it will only process the last 'image' key in the
      multipart body, silently discarding earlier files. Only one photo is saved
      even when the user selects multiple.
    artifacts:
      - path: "frontend/src/views/owner/ShopSetupPage.vue"
        issue: >
          uploadPhotosMutation sends all files in one POST (lines 104-112).
          Needs one POST per file, or the backend endpoint needs to accept
          multiple images in a single request.
      - path: "backend/apps/shops/views.py"
        issue: >
          ShopPhotoView.post (line 120) passes request.data directly to
          ShopPhotoSerializer — only one 'image' field is read.
    missing:
      - "Loop over files in uploadPhotosMutation and issue one POST per file, OR"
      - "Update ShopPhotoSerializer + ShopPhotoView.post to accept and save
         multiple images in a single request"
human_verification:
  - test: "Barber bio display on public profile page"
    expected: >
      Bio entered in barber Settings page appears on whatever public-facing
      profile page customers use to browse barbers (Phase 3 concern, but
      verifying the data round-trips correctly now).
    why_human: >
      Bio is stored and editable (SettingsContent.vue + UserProfileSerializer)
      but no customer-facing barber profile view exists yet. Confirming the
      data persists correctly requires a live test or Phase 3.
  - test: "Shop wizard multi-photo upload (post-fix)"
    expected: >
      Selecting 3 photos in Step 3 of the shop creation wizard results in 3
      photos appearing in ShopManagePage after creation.
    why_human: >
      The current code sends all photos in one request; fix requires either
      frontend or backend change. Needs manual end-to-end test after fix.
---

# Phase 2: Core Entities Verification Report

**Phase Goal:** Shop owners can register and manage their shops, and barbers can set up their full profiles with service catalogs — all data that booking depends on is in place
**Verified:** 2026-03-28
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Shop owner can create a barbershop with name, address, lat/lng, hours, description, and photos (SHOP-01) | PARTIAL | Shop, ShopHours, ShopPhoto models fully wired; frontend wizard collects and POSTs all fields; photo upload sends multiple files in one request but backend only saves one |
| 2 | Shop owner can add/remove barbers under their shop (SHOP-02) | VERIFIED | BarberShopMembership model + POST/DELETE /api/shops/{id}/members/ + ShopManagePage.vue wired end-to-end; tests pass |
| 3 | Barber can create profile with bio, photo, and service catalog with name/price/duration (BARB-01) | VERIFIED | CustomUser.bio + avatar on profile; Service model with name/price/duration_minutes; ServiceModal.vue + /api/services/ wired; bio editable in SettingsContent.vue (barber-only section) |
| 4 | Barber can set weekly availability schedule (BARB-02) | VERIFIED | WeeklySchedule model; GET/PUT /api/availability/schedule/; WeeklyScheduleEditor.vue + AvailabilityPage.vue fully wired; tests pass |
| 5 | Barber can block specific dates/times as unavailable (BARB-03) | VERIFIED | DateBlock model; GET/POST /api/availability/blocks/; DELETE /api/availability/blocks/{pk}/; DateBlockCalendar.vue fully wired; tests pass |

**Score:** 4/5 truths fully verified (1 partial due to multi-photo upload bug)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/apps/shops/models.py` | Shop, ShopHours, ShopPhoto, BarberShopMembership models | VERIFIED | All four models present with correct fields: name, address, lat/lng, description, hours (7-day with open/close/break), photos (ImageField), membership (shop+barber FK) |
| `backend/apps/shops/views.py` | CRUD views for shop, hours, photos, memberships | VERIFIED | ShopCreateView, ShopMeView, ShopDetailView, ShopHoursView, ShopPhotoView, MembershipView — all implemented with owner checks |
| `backend/apps/shops/urls.py` | URL routing for shops app | VERIFIED | All 8 URL patterns registered; included in config/urls.py under api/shops/ |
| `backend/apps/services/models.py` | Service, WeeklySchedule, DateBlock models | VERIFIED | All three models with correct fields; Service has name/price/duration_minutes/sort_order; WeeklySchedule has 7-day with is_working/start_time/end_time/break; DateBlock has date/block_start/block_end/reason |
| `backend/apps/services/views.py` | Service CRUD, reorder, schedule, blocks views | VERIFIED | ServiceListCreateView, ServiceDetailView, ServiceReorderView, WeeklyScheduleView, DateBlockListCreateView, DateBlockDetailView — all implemented with IsBarber permission |
| `backend/apps/services/urls.py` | URL routing for services and availability | VERIFIED | Two URL pattern groups (services_urlpatterns, availability_urlpatterns) both included in config/urls.py |
| `backend/apps/users/models.py` | CustomUser with bio, avatar fields | VERIFIED | bio (TextField), avatar (ImageField), years_of_experience present on CustomUser |
| `frontend/src/views/owner/ShopSetupPage.vue` | 3-step wizard to create shop | VERIFIED | 3 steps: details (name/address/lat/lng/description), hours (7-day editor), photos; submits to POST /api/shops/ then PUT hours then POST photos |
| `frontend/src/views/owner/ShopManagePage.vue` | Shop management with barber add/remove | VERIFIED | Loads shop via GET /api/shops/my/; renders hours, photos, barbers; add/remove barber wired to POST/DELETE /api/shops/{id}/members/ |
| `frontend/src/components/shop/ShopWizardStep1.vue` | Shop details form | VERIFIED | name, address, lat, lng, description fields with v-model via emit |
| `frontend/src/components/shop/ShopWizardStep2.vue` | Hours editor | VERIFIED (exists) | Hours per-day editor component |
| `frontend/src/components/shop/ShopWizardStep3.vue` | Photo upload step | STUB (partial) | File picker with preview works; but upload in parent sends all files in one POST — only one will be persisted |
| `frontend/src/views/barber/ProfileSetupPage.vue` | Barber photo upload | VERIFIED | Fetches profile, uploads avatar via PATCH /api/auth/profile/ multipart; single-file upload is correct |
| `frontend/src/views/barber/ServicesPage.vue` | Service catalog management | VERIFIED | Fetches services via GET /api/services/; openAddModal/openEditModal wired to ServiceModal; ServiceList with drag-to-reorder |
| `frontend/src/components/services/ServiceModal.vue` | Add/edit/delete service form | VERIFIED | Name, price, duration fields; POST /api/services/ (add) or PATCH /api/services/{id}/ (edit); DELETE for edit mode |
| `frontend/src/components/services/ServiceList.vue` | Draggable service list | VERIFIED | vuedraggable; PATCH /api/services/reorder/ on drag end |
| `frontend/src/views/barber/AvailabilityPage.vue` | Weekly schedule + date blocks | VERIFIED | WeeklyScheduleEditor wired with GET/PUT /api/availability/schedule/; DateBlockCalendar component embedded |
| `frontend/src/components/availability/WeeklyScheduleEditor.vue` | 7-day schedule editor | VERIFIED | Toggle per day; start/end/break times; emits update:modelValue |
| `frontend/src/components/availability/DateBlockCalendar.vue` | Calendar for blocking dates | VERIFIED | v-calendar with highlighted blocked dates; POST /api/availability/blocks/ (full-day and time-range); DELETE /api/availability/blocks/{id}/ |
| `frontend/src/components/settings/SettingsContent.vue` | Profile settings including bio | VERIFIED | Bio and years_of_experience fields shown only when role === 'BARBER'; PATCH /api/auth/profile/ wired |
| `frontend/src/router/index.ts` | Routes for all phase-2 pages | VERIFIED | /owner/shop/setup, /owner/shop, /barber/profile, /barber/services, /barber/availability all registered with correct role guards |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| ShopSetupPage.vue | POST /api/shops/ | api.post('/api/shops/', payload) | WIRED | createShopMutation called in handleSubmit, response.data.id used for follow-up calls |
| ShopSetupPage.vue | PUT /api/shops/{id}/hours/ | api.put(\`/api/shops/${shopId}/hours/\`, hours) | WIRED | updateHoursMutation chained after shop creation |
| ShopSetupPage.vue | POST /api/shops/{id}/photos/ | api.post(\`/api/shops/${shopId}/photos/\`, form) | PARTIAL | Called correctly but sends all files in one multipart body; backend only picks up one image |
| ShopManagePage.vue | GET /api/shops/my/ | api.get('/api/shops/my/') | WIRED | useQuery fetches on mount; response rendered (name, address, hours, members) |
| ShopManagePage.vue | POST /api/shops/{id}/members/ | api.post(\`.../members/\`, {barber_id}) | WIRED | addBarber mutation; invalidates shop query on success |
| ShopManagePage.vue | DELETE /api/shops/{id}/members/{id}/ | api.delete(\`.../members/${barberId}/\`) | WIRED | removeBarber mutation; invalidates shop query on success |
| ServicesPage.vue | GET /api/services/ | api.get('/api/services/') | WIRED | useQuery; renders via ServiceList |
| ServiceModal.vue | POST /api/services/ | api.post('/api/services/', payload) | WIRED | saveMutation in add mode |
| ServiceModal.vue | PATCH /api/services/{id}/ | api.patch('/api/services/{id}/', payload) | WIRED | saveMutation in edit mode |
| ServiceModal.vue | DELETE /api/services/{id}/ | api.delete('/api/services/{id}/') | WIRED | deleteMutation in edit mode |
| ServiceList.vue | PATCH /api/services/reorder/ | api.patch('/api/services/reorder/', order) | WIRED | reorderMutation on drag end |
| AvailabilityPage.vue | GET /api/availability/schedule/ | api.get('/api/availability/schedule/') | WIRED | useQuery; result synced into scheduleData via watch |
| AvailabilityPage.vue | PUT /api/availability/schedule/ | api.put('/api/availability/schedule/', schedule) | WIRED | saveMutation in onSaveSchedule; result invalidates query |
| DateBlockCalendar.vue | GET /api/availability/blocks/ | api.get('/api/availability/blocks/') | WIRED | useQuery; calendarAttributes computed from blocks |
| DateBlockCalendar.vue | POST /api/availability/blocks/ | api.post('/api/availability/blocks/', payload) | WIRED | createBlockMutation for full-day and time-range |
| DateBlockCalendar.vue | DELETE /api/availability/blocks/{id}/ | api.delete(\`.../blocks/${blockId}/\`) | WIRED | deleteBlockMutation on remove |
| ProfileSetupPage.vue | GET /api/auth/profile/ | api.get('/api/auth/profile/') | WIRED | useQuery; profile data rendered |
| ProfileSetupPage.vue | PATCH /api/auth/profile/ | api.patch('/api/auth/profile/', formData) | WIRED | uploadMutation with multipart FormData for avatar |
| SettingsContent.vue | PATCH /api/auth/profile/ | api.patch('/api/auth/profile/', payload) | WIRED | saveProfile mutation; bio included when role === BARBER |

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| SHOP-01 | Shop owner can create barbershop with name, address, lat/lng, hours, description, photos | PARTIAL | All fields stored and served; shop creation wizard fully wired; photo upload during setup wizard has multi-file bug (only last photo saved per POST) |
| SHOP-02 | Shop owner can add/remove barbers under their shop | SATISFIED | BarberShopMembership model + POST/DELETE endpoints + ShopManagePage.vue UI; 3 tests passing |
| BARB-01 | Barber can create profile with bio, photo, service catalog (name, price, duration) | SATISFIED | CustomUser.bio+avatar; ProfileSetupPage.vue for photo; SettingsContent.vue for bio (barber-only); Service model + ServiceModal.vue for catalog |
| BARB-02 | Barber can set weekly availability schedule | SATISFIED | WeeklySchedule model; GET/PUT /api/availability/schedule/; WeeklyScheduleEditor.vue; 2 tests passing |
| BARB-03 | Barber can block specific dates/times as unavailable | SATISFIED | DateBlock model; GET/POST/DELETE /api/availability/blocks/; DateBlockCalendar.vue; 2 tests passing |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `frontend/src/views/owner/ShopSetupPage.vue` | 105-110 | `files.forEach((f) => form.append('image', f))` in single POST | Warning | Multi-photo upload during setup wizard silently saves only one photo |
| `frontend/src/views/owner/OverviewPage.vue` | 43 | `<!-- Placeholder table -->` with hardcoded 0 stats | Info | Overview dashboard is a static shell with no real data; expected for Phase 2 (booking data is Phase 3) |

### Human Verification Required

#### 1. Barber bio round-trip

**Test:** Log in as a barber, go to /barber/settings, enter a bio, save. Log in as a different user and (once Phase 3 exposes a barber profile endpoint) verify the bio is present.
**Expected:** Bio entered in settings persists to the database and will be served to customers.
**Why human:** No customer-facing barber profile view exists yet. Can verify storage (bio is in UserProfileSerializer and CustomUser model), but end-to-end display requires Phase 3.

#### 2. Multi-photo upload bug (shop setup wizard)

**Test:** Complete the shop setup wizard, select 3 photos in Step 3, submit. Navigate to /owner/shop and inspect the photos section.
**Expected (current, broken):** Only 1 photo appears despite selecting 3.
**Expected (after fix):** All 3 photos appear.
**Why human:** Confirms the bug is real and validates the fix once applied.

---

## Gaps Summary

One functional gap blocks full SHOP-01 satisfaction:

**Photo upload wiring mismatch in shop setup wizard.** `ShopSetupPage.vue` collects multiple photo files and sends them all in a single multipart POST to `/api/shops/{id}/photos/`, appending each file under the `'image'` key. The backend `ShopPhotoView.post` passes `request.data` directly to `ShopPhotoSerializer`, which only reads a single `ImageField`. DRF's `MultiPartParser` will expose only the last `image` value, causing all but the final selected photo to be silently dropped.

The fix is straightforward — either iterate photos client-side and issue one POST per file, or change the backend to loop over `request.FILES.getlist('image')` and create one `ShopPhoto` per entry.

All other requirements (SHOP-02, BARB-01, BARB-02, BARB-03) are fully satisfied with correct backend models, serializers, views, URL routing, and connected frontend components. The full test suite (32 tests) passes.

---

_Verified: 2026-03-28_
_Verifier: Claude (gsd-verifier)_
