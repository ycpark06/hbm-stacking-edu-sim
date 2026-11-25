import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
plt.rcParams["font.family"]="Noto Sans CJK JP"
LW=1.1
class Sheet:
    def __init__(s,title,no,material,finish,mass,scale="1:1"):
        s.fig,s.a=plt.subplots(figsize=(16.54,11.69)); a=s.a; a.set_xlim(0,420); a.set_ylim(0,297); a.set_aspect("equal"); a.axis("off")
        a.add_patch(Rectangle((10,10),400,277,fill=False,lw=1.6))
        # title block
        x0,y0=250,10
        a.add_patch(Rectangle((x0,y0),160,42,fill=False,lw=1.2))
        for y in (24,38): a.plot([x0,410],[y0+y-10,y0+y-10],color="k",lw=.6)
        a.plot([x0+80,x0+80],[y0,y0+28],color="k",lw=.6)
        a.text(x0+3,y0+36,title,fontsize=12,weight="bold",va="center")
        a.text(x0+3,y0+21,f"재질: {material}",fontsize=7.5,va="center"); a.text(x0+83,y0+21,f"도면 번호: {no}",fontsize=7.5,va="center")
        a.text(x0+3,y0+7,f"표면처리: {finish}",fontsize=7.5,va="center"); a.text(x0+83,y0+7,f"척도 {scale} · 단위 mm · 3각법 · 질량 {mass}",fontsize=7,va="center")
        a.text(x0+3,y0+47,"MSE489 교육용 데스크톱 다이본더",fontsize=7,color="#555")
        a.text(12,14,"일반 공차: ISO 2768-mK  ·  지시 없는 모서리: C0.3 모따기  ·  지시 없는 표면 거칠기: Ra 1.6",fontsize=7)
    def rect(s,x,y,w,h,lw=LW,ls="-"): s.a.add_patch(Rectangle((x,y),w,h,fill=False,lw=lw,ls=ls))
    def circ(s,x,y,r,lw=LW,ls="-"): s.a.add_patch(Circle((x,y),r,fill=False,lw=lw,ls=ls))
    def line(s,x1,y1,x2,y2,lw=LW,ls="-",c="k"): s.a.plot([x1,x2],[y1,y2],color=c,lw=lw,ls=ls)
    def center(s,x1,y1,x2,y2): s.line(x1,y1,x2,y2,lw=.5,ls=(0,(8,2,1,2)),c="#444")
    def dim(s,x1,y1,x2,y2,text,off=6,horiz=True,fs=7.5):
        a=s.a
        if horiz:
            y=max(y1,y2)+off if off>0 else min(y1,y2)+off
            a.plot([x1,x1],[y1,y],color="k",lw=.4); a.plot([x2,x2],[y2,y],color="k",lw=.4)
            a.annotate("",(x1,y),(x2,y),arrowprops=dict(arrowstyle="<->",lw=.6,shrinkA=0,shrinkB=0))
            a.text((x1+x2)/2,y+1,text,ha="center",va="bottom",fontsize=fs)
        else:
            x=max(x1,x2)+off if off>0 else min(x1,x2)+off
            a.plot([x1,x],[y1,y1],color="k",lw=.4); a.plot([x2,x],[y2,y2],color="k",lw=.4)
            a.annotate("",(x,y1),(x,y2),arrowprops=dict(arrowstyle="<->",lw=.6,shrinkA=0,shrinkB=0))
            a.text(x+1,(y1+y2)/2,text,ha="left",va="center",fontsize=fs,rotation=90)
    def leader(s,x,y,tx,ty,text,fs=7.2):
        s.a.annotate(text,(x,y),(tx,ty),fontsize=fs,va="center",arrowprops=dict(arrowstyle="->",lw=.5),bbox=dict(fc="white",ec="none",pad=.3))
    def fcf(s,x,y,cells,fs=7.2):
        # feature control frame: list of strings
        w=[7 if c in ("FLAT","POS") else max(7,len(c)*2.3+3) for c in cells]; X=x
        for c,ww in zip(cells,w):
            s.a.add_patch(Rectangle((X,y),ww,6,fill=False,lw=.7))
            if c=="FLAT":
                s.a.plot([X+1.5,X+4.5,X+ww-1.5,X+ww-4.5,X+1.5],[y+1.8,y+4.2,y+4.2,y+1.8,y+1.8],color="k",lw=.7)
            elif c=="POS":
                s.a.add_patch(Circle((X+ww/2,y+3),1.6,fill=False,lw=.7)); s.a.plot([X+ww/2-2.6,X+ww/2+2.6],[y+3,y+3],color="k",lw=.6); s.a.plot([X+ww/2,X+ww/2],[y+0.4,y+5.6],color="k",lw=.6)
            else: s.a.text(X+ww/2,y+3,c,ha="center",va="center",fontsize=fs)
            X+=ww
        return X
    def datum(s,x,y,letter,dirn="down"):
        s.a.add_patch(Rectangle((x-3,y-12 if dirn=="down" else y+6),6,6,fill=False,lw=.7))
        s.a.text(x,y-9 if dirn=="down" else y+9,letter,ha="center",va="center",fontsize=7.5,weight="bold")
        s.line(x,y,x,y-6 if dirn=="down" else y+6,lw=.7)
        s.a.plot([x-2,x+2,x,x-2],[y,y,y-2.5 if dirn=="down" else y+2.5,y],color="k",lw=.7)
    def rough(s,x,y,ra,fs=6.8):
        s.a.plot([x-2.5,x,x+5],[y+3,y,y+7],color="k",lw=.7); s.a.plot([x+5,x+12],[y+7,y+7],color="k",lw=.7)
        s.a.text(x+6,y+8,ra,fontsize=fs,va="bottom")
    def note(s,x,y,lines,fs=7.4,title="주기"):
        s.a.text(x,y,title,fontsize=8.5,weight="bold",va="top")
        for i,l in enumerate(lines): s.a.text(x,y-6-i*5,l,fontsize=fs,va="top")
    def label(s,x,y,t): s.a.text(x,y,t,fontsize=8.5,weight="bold",ha="center")
    def save(s,fn): s.fig.savefig(fn,dpi=150,bbox_inches="tight",pad_inches=0.1); plt.close(s.fig)
