// 중간 소스/build.js를 복사해 확장: pptxgenjs, native objects, notes, objectName 유지.
// HTML 추출 slides.json 대신 개인정보 없는 deck.json에서 직접 그린다.
'use strict';
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const ROOT = path.resolve(__dirname, '../..');
const D = JSON.parse(fs.readFileSync(path.join(__dirname, 'deck.json'), 'utf8'));
const C = { navy:'14365A', bg:'F5F7FA', orange:'C2622A', peach:'F2A66E', ink:'44505F', muted:'7A8899', stripe:'E6ECF3', pale:'C9D6E6' };
const FONT = 'Malgun Gothic';
async function main() {
  const args = process.argv.slice(2); let local, out;
  while (args.length) { const a=args.shift(); if(!['--cover-local','--out'].includes(a)||!args[0]||args[0].startsWith('--')) throw Error('사용법: node build.js [--cover-local JSON경로 --out PPTX경로]'); if(a==='--cover-local') local=args.shift(); else out=args.shift(); }
  if(local&&!out) throw Error('제출용은 저장소 밖 --out 경로를 지정해야 합니다');
  const target=path.resolve(out||path.join(__dirname,'MSE489_기말발표.pptx'));
  if(!target.endsWith('.pptx')) throw Error('--out 확장자는 .pptx여야 합니다');
  let members;
  if(local) {
    const rel=path.relative(ROOT,target);
    if(rel===''||(!rel.startsWith('..'+path.sep)&&rel!=='..'&&!path.isAbsolute(rel))) throw Error('개인정보 보호: 제출용은 저장소 밖에만 출력합니다');
    const cover=JSON.parse(fs.readFileSync(path.resolve(local),'utf8'));
    if(!Array.isArray(cover.members)||!cover.members.length||cover.members.some(m=>typeof m.name!=='string'||typeof m.id!=='string'||!m.name.trim()||!m.id.trim())) throw Error('members 배열의 name/id 문자열이 필요합니다');
    members=cover.members.map(m=>`${m.name}  ${m.id}`).join('\n');
  }
  const p=new pptxgen(); p.defineLayout({name:'MSE489',width:13.333,height:7.5}); p.layout='MSE489';
  p.title=D.title; p.author='MSE489'; p.subject='교육용 적층 공정 비교 디지털 트윈'; p.company='MSE489'; p.lang='ko-KR';
  p.theme={headFontFace:FONT,bodyFontFace:FONT,lang:'ko-KR'};
  if(D.slides.length!==8) throw Error('슬라이드는 8장이어야 합니다');
  for(const [index,d] of D.slides.entries()) {
    const s=p.addSlide(); const dark=['cover','wrap'].includes(d.id); s.background={color:dark?C.navy:C.bg}; let n=0;
    const name=k=>`${d.id}_${k}${++n}`;
    const text=(t,x,y,w,h,size=18,opts={})=>s.addText(t,{x,y,w,h,fontFace:FONT,fontSize:size,color:dark?C.bg:C.ink,margin:0,breakLine:false,valign:'mid',fit:'none',...opts,objectName:name(opts.bold?'title':'text')});
    const box=(x,y,w,h,fill)=>s.addShape(p.ShapeType.rect,{x,y,w,h,fill:{color:fill},line:{color:fill,transparency:100},objectName:name('box')});
    const img=(f,x,y,w,h)=>{const file=path.join(__dirname,'fig',f); const b=fs.readFileSync(file); const iw=b.readUInt32BE(16),ih=b.readUInt32BE(20),sc=Math.min(w/iw,h/ih);s.addImage({path:file,x:x+(w-iw*sc)/2,y:y+(h-ih*sc)/2,w:iw*sc,h:ih*sc,altText:d.imageAlt||f,objectName:name('img')});};
    const table=(rows,colW,y,rowH,size=18)=>{
      s.addTable(rows.map((r,i)=>r.map(t=>({text:t,options:{bold:i===0,color:i===0?C.bg:C.ink,fill:i===0?C.navy:(i%2?C.stripe:C.bg)}}))),{x:.89,y,w:11.55,h:rowH.reduce((a,b)=>a+b,0),colW,rowH,fontFace:FONT,fontSize:size,margin:[.07,.12,.07,.12],valign:'middle',border:{type:'solid',pt:.6,color:C.pale},autoPage:false,objectName:name('table')});
    };
    text(`${String(index+1).padStart(2,'0')}  ${d.source}`,.89,.52,11.55,.3,13,{bold:true,color:dark?C.peach:C.orange});
    if(d.id!=='cover')text(d.title,.89,1.02,11.55,.65,32,{bold:true,color:dark?C.bg:C.navy});
    text(`${index+1} / 8 · ${d.footer}`,.89,d.id==='results'?7.05:6.88,11.55,.25,12,{color:dark?C.pale:C.muted});
    if(d.id==='cover') {
      text(d.title,.89,1.65,6.1,1.6,44,{bold:true});
      text(d.subtitle,.89,3.45,6.1,.8,24,{color:C.peach});
      text(d.course,.89,4.65,6.1,.8,18);
      text(members||d.publicCover,.89,5.55,6.1,.95,18,{color:C.pale});
      img(d.image,7.25,1.65,5.2,4.8);
    } else if(d.id==='scope') {
      text(d.intro,.89,1.95,11.55,.55,22,{bold:true,color:C.navy});
      table(d.rows,[2.05,4.75,4.75],2.85,[.6,.9,.9,.9],20);
      text(d.statement,.89,6.35,11.55,.35,18);
    } else if(d.id==='system') {
      img(d.image,.89,1.95,4.15,3.8);
      text(d.imageCaption,.89,5.85,4.15,.5,18);
      // 명시 요청된 편집 가능한 구조도. 화살표 대신 두 갈래 선과 순서 배치.
      const blocks=d.blocks;
      for(const b of blocks){box(b.x,b.y,b.w,b.h,C.stripe);text(b.text,b.x+.15,b.y+.05,b.w-.3,b.h-.1,18,{align:'center',bold:true,color:C.navy});}
      for(const l of d.links)s.addShape(p.ShapeType.line,{x:l[0],y:l[1],w:l[2],h:l[3],line:{color:C.navy,width:1.5},objectName:name('box')});
      text(d.caveat,5.45,5.85,6.99,.55,18);
    } else if(d.id==='results') {
      // Mac 대체 글꼴: 장면 열 확대, 모든 수치 행에 두 줄 + 세로 여유 확보.
      table(d.rows,[.9,1.75,5.9,3],1.8,[.5,.9,.8,.8,.82,.9],18);
      text(d.legend,.89,6.65,11.55,.3,18,{color:C.orange});
    } else if(d.id==='trouble') {
      table(d.rows,[2.55,2.8,3.2,3],1.95,[.5,.82,.82,.82],18);
      text(d.metricLabel,.89,5.03,4.65,.35,18);
      text(d.metric,.89,5.48,4.65,.6,32,{bold:true,color:C.navy});
      text(d.metricCaption,.89,6.22,4.65,.35,18);
      text(d.principle,5.65,5.12,6.79,.55,24,{bold:true,color:C.orange});
      text(d.caption,5.65,5.84,6.79,.65,18);
    } else if(d.id==='improve') {
      table(d.rows,[2.05,4.1,5.4],1.95,[.5,.57,.57,.57,.57,.57,.57,.57],18);
    } else if(d.id==='demo') {
      d.steps.forEach((t,i)=>{let x=.89+i*2.36;box(x,2.25,2.1,1.65,C.stripe);text(String(i+1),x+.16,2.43,1.78,.4,26,{bold:true,color:i===0?C.orange:C.navy});text(t,x+.16,3,1.78,.65,20,{bold:true,color:C.navy});if(i<4)s.addShape(p.ShapeType.chevron,{x:x+2.13,y:2.96,w:.2,h:.28,fill:{color:C.navy},line:{color:C.navy},objectName:name('box')});});
      text(d.url,.89,4.55,11.55,.9,26,{bold:true,color:C.navy,hyperlink:{url:d.url}});
      text(d.statement,.89,5.9,11.55,.65,20);
    } else if(d.id==='wrap') {
      text(d.labels[0],.89,2,6.55,.4,22,{bold:true,color:C.peach});text(d.labels[1],8.35,2,4.1,.4,22,{bold:true});
      d.limits.forEach((t,i)=>text(t,.89,2.65+i*.55,6.95,.48,20));
      d.tests.forEach((t,i)=>text(t,8.35,2.65+i*.55,4.1,.48,20));
      text(d.conclusion,.89,5.95,11.55,.6,28,{bold:true});
    }
    s.addNotes(d.notes);
  }
  await p.writeFile({fileName:target}); console.log(local?'제출용 빌드 완료 (경로·개인정보 출력 생략)':'공개판 빌드 완료: '+path.basename(target));
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});
