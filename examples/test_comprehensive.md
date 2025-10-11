# Test All Cases

## Case 1: Should Convert (standalone with colon)

**Performance Concerns:**

Some content after.

## Case 2: Should Convert (standalone without colon)

**Good Design**

Some content after.

## Case 3: Should NOT Convert (label-value with colon)

**Effort:** ~750 LOC, 4-6 weeks
**Risk:** Low-Medium

## Case 4: Should NOT Convert (bold in middle of text)

Some **bold emphasis** in text.

## Case 5: Should NOT Convert (bold at start but with text after, no colon)

**Just Bold Text** in middle of paragraph is not a heading.

## Case 6: Edge case - standalone at end of file

**Final Heading:**
