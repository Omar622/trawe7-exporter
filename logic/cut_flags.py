from typing import List, Tuple, Literal

FlagType = Literal['begin', 'end']
Flag = Tuple[float, FlagType]

def add_flag(flags: List[Flag], time: float, flag_type: FlagType, tol: float = 0.01) -> List[Flag]:
    """Add a flag (time, type) if not present (within tol and type). Returns a sorted list."""
    if not any(abs(f[0] - time) < tol and f[1] == flag_type for f in flags):
        flags.append((time, flag_type))
    return sorted(flags)

def remove_flag(flags: List[Flag], time: float, flag_type: FlagType, tol: float = 0.5) -> List[Flag]:
    """Remove a flag near the given time and type (within tol). Returns a sorted list."""
    new_flags = [f for f in flags if not (abs(f[0] - time) < tol and f[1] == flag_type)]
    return sorted(new_flags)

def toggle_flag(flags: List[Flag], time: float, flag_type: FlagType, tol: float = 0.5) -> List[Flag]:
    """Add if not present, remove if present (within tol and type). Returns a sorted list."""
    if any(abs(f[0] - time) < tol and f[1] == flag_type for f in flags):
        return remove_flag(flags, time, flag_type, tol)
    else:
        return add_flag(flags, time, flag_type, tol)

def validate_flags(flags: List[Flag]) -> bool:
    """
    Validate that flags are alternating [begin, end, begin, end, ...],
    and that each segment (begin < end) does not overlap with the next.
    Returns True if valid, False otherwise.
    """
    if not flags:
        return True
    sorted_flags = sorted(flags)
    # Must start with 'begin'
    if sorted_flags[0][1] != 'begin':
        return False
    for i in range(1, len(sorted_flags)):
        prev_time, prev_type = sorted_flags[i-1]
        curr_time, curr_type = sorted_flags[i]
        # Types must alternate
        if prev_type == curr_type:
            return False
        # begin must be before end
        if prev_type == 'begin' and curr_type == 'end':
            if prev_time >= curr_time:
                return False
        # end must be before next begin
        if prev_type == 'end' and curr_type == 'begin':
            if prev_time >= curr_time:
                return False
    # Must end with 'end' if not empty
    if sorted_flags[-1][1] != 'end':
        return False
    return True
