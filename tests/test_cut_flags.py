from logic.cut_flags import add_flag, remove_flag, toggle_flag, FlagType, Flag, validate_flags

def test_add_flag():
    flags: list[Flag] = []
    # Add begin
    flags = add_flag(flags, 5.0, 'begin')
    assert flags == [(5.0, 'begin')]
    # Add end
    flags = add_flag(flags, 10.0, 'end')
    assert flags == [(5.0, 'begin'), (10.0, 'end')]
    # Add duplicate (should not add)
    flags2 = add_flag(flags.copy(), 5.0, 'begin')
    assert flags2 == flags
    # Add near (within tol, should not add)
    flags3 = add_flag(flags.copy(), 5.005, 'begin', tol=0.01)
    assert flags3 == flags
    # Add same time, different type
    flags4 = add_flag(flags.copy(), 5.0, 'end')
    assert (5.0, 'end') in flags4

def test_remove_flag():
    flags: list[Flag] = [(5.0, 'begin'), (10.0, 'end')]
    # Remove begin
    flags2 = remove_flag(flags, 5.0, 'begin')
    assert flags2 == [(10.0, 'end')]
    # Remove end
    flags3 = remove_flag(flags2, 10.0, 'end')
    assert flags3 == []
    # Remove near (within tol)
    flags4 = remove_flag([(5.0, 'begin')], 5.005, 'begin', tol=0.01)
    assert flags4 == []
    # Remove wrong type (should not remove)
    flags5 = remove_flag([(5.0, 'begin')], 5.0, 'end')
    assert flags5 == [(5.0, 'begin')]

def test_toggle_flag():
    flags: list[Flag] = []
    # Toggle add
    flags = toggle_flag(flags, 5.0, 'begin')
    assert flags == [(5.0, 'begin')]
    # Toggle remove
    flags = toggle_flag(flags, 5.0, 'begin')
    assert flags == []
    # Toggle add different type
    flags = toggle_flag(flags, 5.0, 'end')
    assert flags == [(5.0, 'end')]
    # Toggle add at new time
    flags = toggle_flag(flags, 10.0, 'begin')
    assert (10.0, 'begin') in flags
    # Toggle remove near (within tol)
    flags = toggle_flag(flags, 10.005, 'begin', tol=0.01)
    assert (10.0, 'begin') not in flags

def test_validate_flags():
    # Valid: [begin, end]
    assert validate_flags([(1.0, 'begin'), (2.0, 'end')])
    # Valid: [begin, end, begin, end]
    assert validate_flags([(1.0, 'begin'), (2.0, 'end'), (3.0, 'begin'), (4.0, 'end')])
    # Invalid: starts with end
    assert not validate_flags([(1.0, 'end'), (2.0, 'begin')])
    # Invalid: ends with begin
    assert not validate_flags([(1.0, 'begin'), (2.0, 'end'), (3.0, 'begin')])
    # Invalid: two begins in a row
    assert not validate_flags([(1.0, 'begin'), (2.0, 'begin'), (3.0, 'end')])
    # Invalid: two ends in a row
    assert not validate_flags([(1.0, 'begin'), (2.0, 'end'), (3.0, 'end')])
    # Invalid: overlap (begin after begin, or end before begin)
    assert not validate_flags([(2.0, 'begin'), (1.0, 'end')])
    # Valid: empty
    assert validate_flags([])
