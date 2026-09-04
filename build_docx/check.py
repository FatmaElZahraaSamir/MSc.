import json, os, re, subprocess, sys
import pymupdf
def floats(doc):
    seen={}
    for i in range(doc.page_count):
        p=doc[i]
        for bl in p.get_text("blocks"):
            m=re.search(r'(?m)^(Fig\. \d|TABLE [IVX]+)', bl[4].strip())
            if m and m.group(1) not in seen:
                col='L' if bl[2]<p.rect.width/2 else ('R' if bl[0]>p.rect.width/2 else 'FULL')
                seen[m.group(1)]=(i+1,col)
    for n in range(1, 6):                 # captions swallowed into a figure block
        k = f'Fig. {n}'
        if k in seen: continue
        for i in range(doc.page_count):
            for bl in doc[i].get_text("blocks"):
                if k + '.' in bl[4]:
                    p = doc[i]
                    col='L' if bl[2]<p.rect.width/2 else ('R' if bl[0]>p.rect.width/2 else 'FULL')
                    seen[k]=(i+1,col); break
            if k in seen: break
    return seen
def build(lead):
    env=dict(os.environ, LEAD=str(lead), HOME='/tmp/sofficehome')
    subprocess.run([sys.executable,'tex2docx.py'],check=True,capture_output=True,env=env)
    subprocess.run('rm -rf /tmp/loout',shell=True)
    subprocess.run(['soffice','-env:UserInstallation=file:///tmp/lo_align','--headless','--norestore',
        '--convert-to','pdf','--outdir','/tmp/loout','Paper.docx'],capture_output=True,env=env,timeout=600)
    return pymupdf.open('/tmp/loout/Paper.pdf')
if __name__=='__main__':
    lead=sys.argv[1] if len(sys.argv)>1 else '12.1'
    want=floats(pymupdf.open('../paper/main.pdf'))
    d=build(lead); g=floats(d)
    miss=[k for k in want if want[k]!=g.get(k)]
    print(f"LEAD={lead}: {d.page_count} pages, {len(want)-len(miss)}/{len(want)} floats")
    for k in sorted(want,key=lambda k:(want[k][0],k)):
        gg=g.get(k); print(f"  {k:10s} p{want[k][0]}/{want[k][1]:4s} -> {('p%d/%s'%gg) if gg else 'MISSING':9s} {'ok' if gg==want[k] else 'DIFF'}")
