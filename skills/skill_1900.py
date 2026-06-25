"""修复类型问题 - cycle 3955"""
def ensure(val, t):
    try:
        return t(val)
    except: return None
def execute(): return {"ready": True}