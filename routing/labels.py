"""Stable human-facing display label helpers for nodes and segments."""


def integer_to_segment_code(n: int) -> str:
    """Convert a 1-based positive integer to a bijective base-26 alphabetic code.

    Examples:
        1 -> 'A'
        26 -> 'Z'
        27 -> 'AA'
        28 -> 'AB'
        52 -> 'AZ'
        53 -> 'BA'
        702 -> 'ZZ'
        703 -> 'AAA'
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError("Segment sequence number must be a positive integer.")
    chars = []
    while n > 0:
        n -= 1
        chars.append(chr(65 + (n % 26)))
        n //= 26
    return "".join(reversed(chars))


def segment_code_to_integer(code: str) -> int:
    """Convert an alphabetic segment code back to its 1-based integer index."""
    if not isinstance(code, str):
        raise ValueError(f"Invalid segment code: {code}")
    clean = code.strip().upper()
    if not clean or not clean.isalpha() or not clean.isupper():
        raise ValueError(f"Invalid segment code: {code}")
    total = 0
    for char in clean:
        total = total * 26 + (ord(char) - 64)
    return total


def is_valid_node_label(label: str) -> bool:
    """Return True if label is a clean positive integer string (e.g. '1', '42')."""
    if not isinstance(label, str):
        return False
    clean = label.strip()
    return bool(clean and clean.isdigit() and int(clean) > 0)


def is_valid_segment_label(label: str) -> bool:
    """Return True if label is a clean uppercase alphabetic code (e.g. 'A', 'ZZ')."""
    if not isinstance(label, str):
        return False
    clean = label.strip().upper()
    return bool(clean and clean.isalpha() and clean.isupper())


def clean_node_label(label: str) -> str:
    """Normalize input node label (e.g. 'Node 5' -> '5', ' 12 ' -> '12')."""
    if not label:
        return ""
    clean = str(label).strip()
    if clean.lower().startswith("node "):
        candidate = clean[5:].strip()
        if candidate.isdigit() and int(candidate) > 0:
            return str(int(candidate))
    if clean.isdigit() and int(clean) > 0:
        return str(int(clean))
    return clean


def clean_segment_label(label: str) -> str:
    """Normalize input segment label (e.g. 'Segment A' -> 'A', ' ab ' -> 'AB')."""
    if not label:
        return ""
    clean = str(label).strip().upper()
    if clean.startswith("SEGMENT "):
        candidate = clean[8:].strip()
        if candidate.isalpha():
            return candidate
    if clean.isalpha():
        return clean
    return clean


def next_node_label(nodes_iterable=None) -> str:
    """Find the highest existing positive integer label and return str(max + 1).

    If no valid numeric labels exist, returns '1'.
    """
    if nodes_iterable is None:
        from .models import WalkableNode
        nodes_iterable = WalkableNode.objects.values_list("label", flat=True)
    max_num = 0
    for label in nodes_iterable:
        if isinstance(label, str) and label.strip().isdigit():
            val = int(label.strip())
            if val > max_num:
                max_num = val
    return str(max_num + 1)


def next_segment_label(segments_iterable=None) -> str:
    """Find the highest existing alphabetic label and return the next code.

    If no valid alphabetic labels exist, returns 'A'.
    """
    if segments_iterable is None:
        from .models import WalkableSegment
        segments_iterable = WalkableSegment.objects.values_list("label", flat=True)
    max_num = 0
    for label in segments_iterable:
        if isinstance(label, str):
            clean = label.strip().upper()
            if clean and clean.isalpha():
                try:
                    num = segment_code_to_integer(clean)
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
    return integer_to_segment_code(max_num + 1)


def classify_route_verification(verification_states) -> str:
    """Classify the user-facing verification state of a route from its constituent elements.

    - If all traversed elements are FIELD_VERIFIED, the route is FIELD_VERIFIED.
    - If all traversed elements are DEMO, the route is DEMO.
    - Otherwise (contains UNVERIFIED, mixed states, or empty), the route is UNVERIFIED.
    """
    clean_states = {str(s).strip() for s in verification_states if s}
    if not clean_states:
        return "UNVERIFIED"
    if clean_states == {"FIELD_VERIFIED"}:
        return "FIELD_VERIFIED"
    if clean_states == {"DEMO"}:
        return "DEMO"
    return "UNVERIFIED"
