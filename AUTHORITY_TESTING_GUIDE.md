# Authority & Admin Features - Quick Test Guide

**Updated**: 2026-06-24  
**Status**: Ready for testing after bug fixes

---

## 🚀 Quick Start Testing

### Prerequisites
- Backend running on http://localhost:8000
- Frontend running on http://localhost:3000
- First admin account created (user ID = 1)
- Database populated with at least one test issue

### Setup (One-time)
```bash
# 1. Make sure backend is running
cd d:\COMMUNITY-HERO\backend
uvicorn app.main:app --reload

# 2. Make sure frontend is running (another terminal)
cd d:\COMMUNITY-HERO\frontend
python -m http.server 3000

# 3. Create admin account (if not already done)
# Option A: SQLite direct
sqlite3 backend/community_hero.db "UPDATE users SET role = 'admin' WHERE id = 1;"

# Option B: Promote via API (after creating first user)
# See ADMIN_QUICK_START.md for detailed instructions
```

---

## 🧪 Test Scenarios

### Test 1: Verify Login Returns Role

**Steps**:
1. Open browser developer console (F12)
2. Go to http://localhost:3000
3. Click "Sign Up" and create test account
4. Note the username/password
5. Click "Login"
6. Check console (Network tab) → Click login request
7. Look at Response → Should see:
   ```json
   {
     "id": 2,
     "username": "test_user",
     "role": "citizen",
     ...
   }
   ```

**Expected**: Response includes `"role": "citizen"`  
**Status**: ✅ PASS if role field present

---

### Test 2: Verify Role Badge Displays

**Steps**:
1. Login as citizen (from Test 1)
2. Check navbar (top right)
3. Should see user pill with username
4. NO role badge for citizen

**Expected**: Citizen = no badge, Authority = "AUTHORITY" badge, Admin = "ADMIN" badge  
**Status**: ✅ PASS

---

### Test 3: Promote User to Authority

**Steps**:
1. Open terminal (or API testing tool)
2. Run this command (replace with your IDs):
   ```bash
   curl -X PUT "http://localhost:8000/api/users/2/role?admin_id=1" \
     -H "Content-Type: application/json" \
     -d '{"role": "authority"}'
   ```
3. Response should show:
   ```json
   {
     "id": 2,
     "role": "authority",
     ...
   }
   ```

**Expected**: User 2 role changed to authority  
**Status**: ✅ PASS

---

### Test 4: Verify Authority Role Badge

**Steps**:
1. Logout (click Logout button)
2. Clear browser cache: Open DevTools → Application → localStorage → delete "ch_user"
3. Login with the promoted authority account
4. Check navbar
5. Should see "AUTHORITY" badge next to username (in indigo/purple color)

**Expected**: Authority badge displays in navbar  
**Status**: ✅ PASS

---

### Test 5: Verify Authority Can Claim Issue

**Prerequisites**: 
- Authority user logged in
- At least one issue exists (REPORTED status)

**Steps**:
1. Go to http://localhost:3000#issues
2. Click on any issue to open details
3. Look for "Claim Issue" button (green button with hand icon)
4. Click "Claim Issue"
5. Should see toast: "Issue assigned to you! +50 reputation points"
6. Buttons change to "In Progress" and "Mark Resolved"

**Expected**: Authority can see and click "Claim Issue"  
**Status**: ✅ PASS if button visible and click succeeds

---

### Test 6: Verify Authority Can Update Status

**Prerequisites**: 
- Issue claimed by authority user (from Test 5)
- Authority user logged in

**Steps**:
1. Same issue from Test 5 should still be open
2. Click "In Progress" button
3. Should see toast: "Issue status updated to in_progress"
4. Buttons should remain visible

**Expected**: Status changes to in_progress  
**Status**: ✅ PASS

---

### Test 7: Verify Authority Can Resolve Issue

**Prerequisites**:
- Issue status is in_progress (from Test 6)
- Authority user logged in

**Steps**:
1. Click "Mark Resolved" button
2. Should see toast: "Issue resolved! +50 reputation points"
3. Issue detail modal closes
4. Refresh to verify issue now shows RESOLVED status

**Expected**: Issue marked as resolved, +50 points awarded  
**Status**: ✅ PASS

---

### Test 8: Verify Resolution History

**Prerequisites**:
- Issue has been through claim → in_progress → resolved (Tests 5-7)

**Steps**:
1. Go back to resolved issue
2. Look for "Resolution History" section
3. Should see entries:
   - REPORTED
   - VERIFIED
   - IN_PROGRESS
   - RESOLVED
4. Each entry shows timestamp

**Expected**: History shows all status changes  
**Status**: ✅ PASS

---

### Test 9: Verify Leaderboard Role Badges

**Steps**:
1. Go to http://localhost:3000#leaderboard
2. Look at leaderboard table
3. Should see role badges:
   - Authority users: Purple "AUTH" badge
   - Admin users: Red "ADMIN" badge
   - Citizen users: No badge

**Expected**: Role badges display correctly in table  
**Status**: ✅ PASS

---

### Test 10: Verify Dashboard Statistics Update

**Prerequisites**:
- Completed issue resolution workflow (Tests 5-7)

**Steps**:
1. Go to http://localhost:3000#dashboard
2. Check statistics:
   - "Total Issues" should include the reported issue
   - "Resolved Issues" should include the resolved issue
   - "Resolution Rate" should increase
   - Authority user should appear in leaderboard with +100 reputation

**Expected**: All statistics update correctly  
**Status**: ✅ PASS

---

## 📋 Complete Testing Checklist

### Pre-Testing
- [ ] Backend running on :8000
- [ ] Frontend running on :3000
- [ ] Admin account created (ID=1 with role=admin)
- [ ] Database initialized with tables
- [ ] At least 1 test issue exists

### Feature Tests
- [ ] Test 1: Login returns role - ✅ PASS / ❌ FAIL
- [ ] Test 2: Role badge displays - ✅ PASS / ❌ FAIL
- [ ] Test 3: Can promote to authority - ✅ PASS / ❌ FAIL
- [ ] Test 4: Authority badge shows - ✅ PASS / ❌ FAIL
- [ ] Test 5: Can claim issue - ✅ PASS / ❌ FAIL
- [ ] Test 6: Can update status - ✅ PASS / ❌ FAIL
- [ ] Test 7: Can resolve issue - ✅ PASS / ❌ FAIL
- [ ] Test 8: Resolution history visible - ✅ PASS / ❌ FAIL
- [ ] Test 9: Leaderboard shows badges - ✅ PASS / ❌ FAIL
- [ ] Test 10: Dashboard stats update - ✅ PASS / ❌ FAIL

### Regression Tests
- [ ] Citizen can still register
- [ ] Citizen can still login
- [ ] Citizen can verify issues
- [ ] Citizen can report issues
- [ ] No errors in browser console
- [ ] No errors in backend logs
- [ ] Session persists on refresh
- [ ] Logout clears session

---

## 🔍 Debugging Tips

### Issue: Role badge not showing after login

**Debug Steps**:
1. Open DevTools → Console
2. Type: `console.log(currentUser)`
3. Check if `role` property exists
4. Should output:
   ```javascript
   {id: 1, username: "test", role: "authority", ...}
   ```

**If role is missing**:
- Backend not updated with login fix
- Clear localStorage: `localStorage.clear()`
- Re-login

### Issue: "Claim Issue" button not visible

**Debug Steps**:
1. Open DevTools → Console
2. Type: `console.log(isAuthority())`
3. Should return: `true` for authority/admin
4. Check navbar - should see role badge

**If isAuthority() returns false**:
- currentUser.role not being set
- See "Role badge not showing" debug above

### Issue: API call failing with 422 error

**Debug Steps**:
1. DevTools → Network tab → look for failed request
2. Click request → Response tab
3. Check error message
4. Common causes:
   - `resolver_id` undefined (use `currentUser.id`)
   - `user_id` undefined (use `currentUser.id`)
   - User doesn't have authority role

### Issue: Issue doesn't update after claiming

**Debug Steps**:
1. Check backend logs for errors
2. Verify issue ID is correct
3. Verify user has authority role
4. Try manually refreshing: `loadIssues(true)`

---

## 🛠️ Common Test Commands

### Check Backend Health
```bash
curl http://localhost:8000/health
```
Expected: `200 OK` with status info

### Test Login Endpoint
```bash
curl -X POST "http://localhost:8000/api/users/login?username=admin&password=admin123"
```
Expected: Full user object with `role` field

### Get All Users (for debugging)
```bash
curl http://localhost:8000/api/users/
```
Expected: Array of users with all roles

### Get Single Issue
```bash
curl http://localhost:8000/api/issues/1
```
Expected: Issue with all resolver fields

### Get Dashboard Stats
```bash
curl http://localhost:8000/api/stats/dashboard
```
Expected: Stats object with counts and rate

---

## ✅ Success Criteria

**All Authority Features Working When**:
- ✅ Login returns user role
- ✅ Role badges display correctly
- ✅ Authority users see claim button
- ✅ Authority users see status buttons
- ✅ API calls succeed with correct parameters
- ✅ Reputation increases after actions
- ✅ Dashboard stats update
- ✅ Leaderboard shows roles correctly

---

## 📞 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Claim Issue" button not visible | Check: `isAuthority()` returns true, role badge shows |
| API returns 403 "Only admins can assign roles" | Correct - only use with admin_id=1 |
| Role badge shows but buttons don't | Clear cache, re-login |
| Issue not updating after claim | Check backend logs, try refresh |
| Leaderboard shows no badges | Ensure roles are set, refresh page |
| Login fails after update | Use correct username/password from signup |

---

## Next Steps After Testing

1. ✅ All tests pass → **System ready for production**
2. ✅ Fix any failing tests → Update backend/frontend
3. ✅ Performance test with multiple users
4. ✅ Deploy to staging environment
5. ✅ User acceptance testing

---

**Last Updated**: 2026-06-24  
**Status**: 🟢 READY FOR TESTING
