# Bulk Cleaner Module (Feature 1)

**Status:** Coming Soon

This module will provide general email cleanup functionality, including:

- Pattern-based deletion for promotional emails
- Newsletter cleanup
- Spam deletion
- Category-based deletion rules

## Why This is Deferred

Feature 2 (Job Tracker) is being built first because:

1. **Priority:** Job tracking is the critical need for the user
2. **Validation:** Want to validate core architecture before extending
3. **Different Patterns:** General cleanup requires different rules than job emails
4. **Testing:** User wants to test Feature 2 thoroughly first

## Shared Components from Core

This module will reuse:

- Gmail client
- Authentication flow
- Deletion logic
- Safety mechanisms
- Configuration system

## Timeline

Development will begin after Feature 2 is validated and tested.

A separate PRD will be created for this feature.
