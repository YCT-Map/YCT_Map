# Stop Conditions

Codex must stop and request owner review when any of the following occurs:

1. A new architectural decision is required.
2. A destructive database operation is required.
3. A production secret is required but unavailable.
4. A migration checksum or historical migration mismatch appears.
5. Existing user data may be lost.
6. Authentication or authorization behavior must materially change.
7. Security would need to be weakened.
8. A paid service appears necessary.
9. A new external provider must be introduced.
10. Git history has unexpected divergence.
11. A force push/rebase/history rewrite appears necessary.
12. Production deployment or migration is required without explicit approval.
13. Tests reveal an unrelated regression.
14. The same external/environment failure occurs twice without new evidence.
15. The requested implementation contradicts an authoritative project document.
16. The repository state differs materially from the expected project state.
17. **YCT Map — Campus Data Integrity:** Implementation requires inventing, inferring or marking as verified a real YabaTech location, building outline, entrance, walkable path, floor or internal destination without trusted project data. If the required real-world information is unknown: use explicitly labelled demo data, mark the record unverified, or request owner/team field verification. Never guess real campus geography.

When stopping:

- preserve repository state;
- avoid speculative fixes;
- report the evidence;
- identify the smallest owner decision needed.
