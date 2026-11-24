"""Correctly map absolute source frames into synopsis frames for a group."""

def group_span(tubes):
    return max(int(t.frames[-1]) for t in tubes)-min(int(t.frames[0]) for t in tubes)+1

def shifted_frames(tube, group_tubes, group_start):
    anchor=min(int(t.frames[0]) for t in group_tubes)
    return [int(group_start)+int(fr)-anchor for fr in tube.frames]

def validate_group_placement(tubes, group_start, synopsis_length):
    if group_start < 0 or group_start + group_span(tubes)>synopsis_length:
        raise ValueError('Group does not fit the synopsis budget')
    return {t.id:shifted_frames(t,tubes,group_start) for t in tubes}

if __name__=='__main__':
    from dataclasses import dataclass
    @dataclass
    class T:
        id:str
        frames:list
    a,b=T('a',[100,102,105]),T('b',[103,104,107])
    got=validate_group_placement([a,b],4,12)
    assert got=={'a':[4,6,9],'b':[7,8,11]},got
    assert group_span([a,b])==8
    try:validate_group_placement([a,b],5,12)
    except ValueError:pass
    else:raise AssertionError('Should reject budget overflow')
    print('PASS: source offsets preserved; exact group span; budget overflow rejected')
