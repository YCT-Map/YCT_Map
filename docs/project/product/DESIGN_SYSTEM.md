# Design System — YCT Map

This document records the approved visual direction for YCT Map.

Implementation has not started. This document defines **approved design intent** to guide future implementation.

Sections are marked:
- APPROVED — owner-confirmed decision
- OPEN — awaiting design decision

---

## Guiding Principles

**APPROVED**

- **Mobile-first.** Designed for ordinary student smartphones on limited mobile data.
- **Map-first interface.** The map is primary. No unnecessary landing page before the map experience.
- **Lightweight.** Minimize data usage and battery consumption.
- **Premium and modern.** Not generic academic-site styling. The product should feel trustworthy and polished.
- **Floating controls.** Search and map controls float over the map surface.
- **Bottom sheets.** Preferred pattern for destination panels, route panels and contribution flows on mobile.

---

## Color Palette

**APPROVED — direction**

Primary colors:
- Green — primary brand color
- White — surfaces, backgrounds
- Grey — secondary text, dividers, inactive states
- Yellow — accent, highlights, warnings

Use these colors with restraint. Avoid overly saturated or clashing combinations.

Exact color tokens (hex / HSL values): OPEN — to be defined during implementation.

---

## Typography

**OPEN**

Modern typography required. Generic browser defaults are not acceptable.

Candidates: Inter, Roboto, or equivalent.
Final choice: OPEN — to be confirmed during implementation.

---

## Spacing and Layout

**OPEN — to be defined during implementation**

Standard spacing scale required to ensure consistency.

---

## Key UI Components

**APPROVED — direction**

| Component | Notes |
|-----------|-------|
| Search bar | Floating over the map; prominent; always accessible |
| Map controls | Floating; minimal footprint |
| Bottom sheet | Primary mobile interaction pattern for destination and route info |
| Destination panel | Shows name, category, description, directions CTA |
| Route panel | Shows distance, estimated time, written guidance |
| Contribution form | Accessible without account; simple |
| Editor dashboard | Authenticated; clean data management interface |

Exact component specification: OPEN — to be designed during implementation.

---

## 3D and Depth Effects

**APPROVED**

Modest 3D or depth effects are permitted.

3D work must not delay or block:
- search functionality;
- routing functionality;
- live location;
- contribution flows;
- editor functionality.

Photorealistic 3D is explicitly out of scope for V1.

---

## Responsive Behavior

**APPROVED**

- Mobile-first.
- Must be fully usable on desktop.
- Bottom-sheet patterns adapt to desktop appropriately.

---

## Icons

**OPEN — icon library to be chosen during implementation**

---

## Motion and Animation

**OPEN**

Subtle micro-animations for enhanced UX are permitted. Must remain lightweight given the battery/data constraints.

---

## Copy and Tone

**OPEN — to be defined**

- Understandable to students and visitors.
- Clear, direct, non-jargon.
- Helpful in empty and error states.
