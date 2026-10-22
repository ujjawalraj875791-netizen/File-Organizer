import json
from organizer.config import DATA, STATE_FILE
class StateStore:
    def __init__(self):
        DATA.mkdir(parents=True,exist_ok=True)
        if not STATE_FILE.exists(): self.save({"operations":[]})
    def load(self):
        try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): return {"operations":[]}
    def save(self,data):
        tmp=STATE_FILE.with_suffix('.tmp'); tmp.write_text(json.dumps(data,indent=2),encoding='utf-8'); tmp.replace(STATE_FILE)
    def push(self,op):
        d=self.load(); d.setdefault('operations',[]).append(op); self.save(d)
    def last(self):
        ops=self.load().get('operations',[]); return ops[-1] if ops else None
    def pop(self):
        d=self.load(); ops=d.setdefault('operations',[])
        if ops: ops.pop(); self.save(d)
