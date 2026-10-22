from pathlib import Path
from datetime import datetime
import hashlib, json, logging, shutil, uuid
from organizer.config import CATEGORIES, LOGS, LOG_FILE
from organizer.exceptions import OrganizerError, UndoError
from organizer.state import StateStore

class FileOrganizer:
    def __init__(self):
        LOGS.mkdir(parents=True,exist_ok=True)
        self.log=logging.getLogger('file_organizer')
        if not self.log.handlers:
            self.log.setLevel(logging.INFO); h=logging.FileHandler(LOG_FILE,encoding='utf-8')
            h.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')); self.log.addHandler(h)
        self.state=StateStore()
    @staticmethod
    def folder(path):
        p=Path(path).expanduser().resolve()
        if not p.is_dir(): raise OrganizerError(f'Folder does not exist: {p}')
        return p
    @staticmethod
    def unique(p):
        if not p.exists(): return p
        n=1
        while True:
            q=p.with_name(f'{p.stem} ({n}){p.suffix}')
            if not q.exists(): return q
            n+=1
    @staticmethod
    def category(p):
        for name,exts in CATEGORIES.items():
            if p.suffix.lower() in exts: return name
        return 'Others'
    @staticmethod
    def digest(p):
        h=hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
        return h.hexdigest()
    def scan(self,folder,recursive=False):
        base=self.folder(folder); it=base.rglob('*') if recursive else base.iterdir(); out=[]
        for p in it:
            try:
                if p.is_file() and not p.is_symlink():
                    s=p.stat(); out.append({'path':str(p),'name':p.name,'category':self.category(p),'size':s.st_size,'modified':datetime.fromtimestamp(s.st_mtime).strftime('%Y-%m-%d %H:%M:%S')})
            except OSError: pass
        return out
    def categorize_preview(self,folder,recursive=False):
        base=self.folder(folder); out=[]
        for r in self.scan(base,recursive):
            src=Path(r['path']); out.append({'source':str(src),'target':str(self.unique(base/r['category']/src.name)),'category':r['category']})
        return out
    def _record(self,kind,moves,root=None):
        op={'id':str(uuid.uuid4()),'type':kind,'timestamp':datetime.now().isoformat(timespec='seconds'),'root':str(root) if root else None,'moves':moves}
        self.state.push(op); self.log.info('%s: %d file moves; operation=%s',kind,len(moves),op['id']); return op
    @staticmethod
    def rollback(moves):
        for m in reversed(moves):
            src,dst=Path(m['to']),Path(m['from'])
            try:
                if src.exists() and not dst.exists(): dst.parent.mkdir(parents=True,exist_ok=True); src.rename(dst)
            except OSError: pass
    def categorize(self,folder,recursive=False):
        base=self.folder(folder); moves=[]
        try:
            for item in self.categorize_preview(base,recursive):
                src,dst=Path(item['source']),Path(item['target'])
                if not src.exists(): continue
                dst.parent.mkdir(parents=True,exist_ok=True); dst=self.unique(dst); shutil.move(str(src),str(dst)); moves.append({'from':str(src),'to':str(dst)})
            return self._record('categorize',moves,base)
        except Exception: self.rollback(moves); raise
    def find_duplicates(self,folder,recursive=True):
        base=self.folder(folder); it=base.rglob('*') if recursive else base.iterdir(); sizes={}
        for p in it:
            try:
                if p.is_file() and not p.is_symlink(): sizes.setdefault(p.stat().st_size,[]).append(p)
            except OSError: pass
        groups={}
        for size,paths in sizes.items():
            if len(paths)<2: continue
            for p in paths:
                try: groups.setdefault((size,self.digest(p)),[]).append(str(p))
                except OSError: pass
        return [{'size':s,'sha256':h,'files':sorted(ps)} for (s,h),ps in groups.items() if len(ps)>1]
    def remove_duplicates(self,groups,keep='first'):
        if keep not in {'first','newest','oldest'}: raise OrganizerError('keep must be first, newest, or oldest')
        moves=[]
        try:
            for g in groups:
                ps=[Path(p) for p in g['files'] if Path(p).is_file()]
                if len(ps)<2: continue
                if keep=='newest': ps.sort(key=lambda p:p.stat().st_mtime,reverse=True)
                elif keep=='oldest': ps.sort(key=lambda p:p.stat().st_mtime)
                else: ps.sort(key=lambda p:str(p).casefold())
                for p in ps[1:]:
                    d=p.parent/'_duplicates'; d.mkdir(exist_ok=True); dest=self.unique(d/p.name); shutil.move(str(p),str(dest)); moves.append({'from':str(p),'to':str(dest)})
            return self._record('move_duplicates',moves)
        except Exception: self.rollback(moves); raise
    @staticmethod
    def rename_name(pattern,index,p):
        ext=p.suffix.lstrip('.'); name=pattern.format(name=p.stem,ext=ext,index=index,date=datetime.now().strftime('%Y%m%d')).strip()
        if not name or name in {'.','..'} or '/' in name or chr(92) in name or '\0' in name: raise OrganizerError('Pattern must produce a filename, not a path.')
        return name if '{ext}' in pattern else name+p.suffix
    def rename_preview(self,folder,pattern,recursive=False,start_index=1):
        files=sorted((Path(r['path']) for r in self.scan(folder,recursive)),key=lambda p:str(p).casefold()); out=[]
        for i,p in enumerate(files,start_index):
            target=p.with_name(self.rename_name(pattern,i,p))
            if target.exists() and target.resolve()!=p.resolve(): target=self.unique(target)
            out.append({'source':str(p),'target':str(target)})
        if len({x['target'].casefold() for x in out})!=len(out): raise OrganizerError('Pattern creates duplicate target names. Change the pattern.')
        return out
    def batch_rename(self,folder,pattern,recursive=False,start_index=1):
        preview=self.rename_preview(folder,pattern,recursive,start_index); staged=[]; moves=[]
        try:
            # Stage all names first so swaps and overlapping names do not collide.
            for item in preview:
                src=Path(item['source'])
                if src.exists():
                    tmp=src.with_name('.__organizer_tmp_'+uuid.uuid4().hex+'__'); src.rename(tmp); staged.append((tmp,Path(item['target']),src))
            for tmp,target,original in staged:
                if target.exists(): target=self.unique(target)
                tmp.rename(target); moves.append({'from':str(original),'to':str(target)})
            return self._record('batch_rename',moves,folder)
        except Exception:
            self.rollback(moves)
            for tmp,target,original in staged:
                if tmp.exists() and not original.exists(): tmp.rename(original)
            raise
    def undo_last(self):
        op=self.state.last()
        if not op: raise UndoError('There is no operation to undo.')
        moves=op.get('moves',[])
        for m in moves:
            if not Path(m['to']).exists(): raise UndoError(f"Cannot undo; expected file missing: {m['to']}")
            if Path(m['from']).exists(): raise UndoError(f"Cannot undo safely; destination already exists: {m['from']}")
        restored=[]
        try:
            for m in reversed(moves):
                cur,old=Path(m['to']),Path(m['from']); old.parent.mkdir(parents=True,exist_ok=True); cur.rename(old); restored.append({'from':str(cur),'to':str(old)})
            self.state.pop(); self.log.info('Undo successful for operation=%s',op['id'])
            return f"Undo successful: restored {len(restored)} file(s) from {op['type']}."
        except Exception: self.rollback(restored); raise
