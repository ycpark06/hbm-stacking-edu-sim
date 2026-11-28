'use strict';
const fs=require('fs'),path=require('path');
const PptxGenJS=require('../node_modules/pptxgenjs');
const JSZip=require('../node_modules/jszip');
const D=JSON.parse(fs.readFileSync(path.join(__dirname,'deck_v2.json'),'utf8'));
const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'numeric_manifest.json'),'utf8'));
const ROOT=path.resolve(__dirname,'../../..');
const C={white:'FFFFFF',navy:'14365A',ink:'44505F',orange:'C2622A',pale:'E6ECF3'};
async function main(){
 const args=process.argv.slice(2);let coverPath,outPath;
 while(args.length){const arg=args.shift(),v=args.shift();if(!v||v.startsWith('--')||!['--cover-json','--out'].includes(arg))throw Error('사용법: node build_v2.js [--cover-json <경로> --out <경로>]');if(arg==='--cover-json')coverPath=v;else outPath=v;}
 if(coverPath&&!outPath)throw Error('로컬 표지는 --out 경로가 필요합니다');
 const output=path.resolve(outPath||path.join(__dirname,'MSE489_기말발표_v2.pptx'));
 if(!output.endsWith('.pptx'))throw Error('출력 확장자는 .pptx여야 합니다');
 let members='';
 if(coverPath){
  const rel=path.relative(ROOT,output);if(!rel.startsWith('..'+path.sep)&&rel!=='..')throw Error('개인 표지는 저장소 밖 --out 경로에 출력해야 합니다');
  const cover=JSON.parse(fs.readFileSync(path.resolve(coverPath),'utf8'));
  if(!Array.isArray(cover.members)||!cover.members.length||cover.members.length>4||cover.members.some(m=>typeof m.name!=='string'||typeof m.id!=='string'||!m.name.trim()||!m.id.trim()||m.name.length>20||m.id.length>20))throw Error('members: [{name, id}] 형식 필요');
  members=cover.members.map(m=>`${m.name}  ${m.id}`).join('\n');
 }
 const p=new PptxGenJS();p.defineLayout({name:'WIDE',width:13.333,height:7.5});p.layout='WIDE';
 p.author='';p.company='';p.title=D.title;p.subject='두 적층 공정의 차이와 실패 원인';p.lang='ko-KR';p.theme={headFontFace:'Pretendard',bodyFontFace:'Pretendard',lang:'ko-KR'};
 const boxes=[];
 for(const [i,d] of D.slides.entries()){
  const s=p.addSlide();s.background={color:C.white};let n=0;
  function text(t,x,y,w,h,size=24,extra={}){boxes.push({slide:i+1,text:t,x,y,w,h,size,bold:!!extra.bold});s.addText(t,{x,y,w,h,fontFace:'Pretendard',fontSize:size,color:C.ink,margin:0,fit:'none',valign:'mid',paraSpaceAfterPt:0,objectName:`${d.id}_text${++n}`,...extra});}
  function image(name,x,y,w,h){const f=path.join(__dirname,'assets',name+'.png');const b=fs.readFileSync(f),iw=b.readUInt32BE(16),ih=b.readUInt32BE(20),k=Math.min(w/iw,h/ih);s.addImage({path:f,x:x+(w-iw*k)/2,y:y+(h-ih*k)/2,w:iw*k,h:ih*k,objectName:`${d.id}_image${++n}`,altText:name});}
  text(d.title,.8,.55,11.75,.72,32,{bold:true,color:C.navy});
  if(d.kind==='architecture'){
   // Explicitly requested editable reconstruction: C, HAL, MCU and wasm only.
   text('共通 C 제어기'.replace('共通','공통'),3.75,2.0,5.8,.65,36,{bold:true,color:C.navy,align:'center'});
   const line=(x,y,w,h)=>s.addShape(p.ShapeType.line,{x,y,w,h,line:{color:C.navy,width:1.8},objectName:`${d.id}_line${++n}`});
   line(6.65,2.8,0,.6);line(3.1,3.4,7.1,0);line(3.1,3.4,0,.5);line(10.2,3.4,0,.5);
   text('MCU HAL',1.0,4,4.4,.6,30,{bold:true,color:C.navy,align:'center'});text('wasm HAL',8.0,4,4.4,.6,30,{bold:true,color:C.navy,align:'center'});
   text('MCU 제어 보드',1.0,4.85,4.4,.5,24,{align:'center'});text('브라우저',8.0,4.85,4.4,.5,24,{align:'center'});
   text(d.body,.96,6.6,11.4,.45,22);
  }else if(d.kind==='repo'){
   image('github',.95,1.7,3.9,4.6);
   text('영상에서 본 저장소',5.4,2.65,6.9,.75,38,{bold:true,color:C.navy});
   text('계산 입력과 검증 기록',5.4,3.6,6.9,.5,26);
   const url='https://github.com/ycpark06/hbm-stacking-edu-sim';const pages='https://ycpark06.github.io/hbm-stacking-edu-sim/web/';
   text([{text:'github.com/ycpark06/hbm-stacking-edu-sim',options:{hyperlink:{url}}},{text:'   /   '},{text:'ycpark06.github.io/hbm-stacking-edu-sim/web/',options:{hyperlink:{url:pages}}}],.8,6.65,11.75,.4,17);
  }else if(d.kind==='judgement'){
   text('결과를 맞추려고\n열저항을 바꾸지 않았다',.96,2.13,11.3,1.85,48,{bold:true,color:C.navy});
   text('미달은 알람으로, 헤드 보정은 선택',.98,5.22,11.2,.55,26);
  }else if(d.kind==='comparison'){
   text('약 231 ℃',.93,1.46,5.9,1.1,66,{bold:true,color:C.orange});text('전 층 자기 접합 최고 온도',7.05,1.87,5.25,.45,24);
   text('층별 최고 온도 (℃)',.96,2.92,6,.32,20);image(d.visual,.8,3.5,11.75,3.7);
  }else if(d.kind==='big'){
   text(d.visual,.95,2.25,11.4,1.65,d.visual.length>10?68:92,{bold:true,color:C.orange});
   const caption=d.outline===19?'비교한 출력값 수':d.body;
   text(caption,.98,4.95,11.25,1.05,28);
  }else if(d.kind==='chart'){
   image(d.visual,.8,1.65,11.75,4.75);text(d.body,.96,6.6,11.4,.45,22);
  }else{
   const narrow=['alarms','pr'].includes(d.visual);image(d.visual,.85,narrow?2.25:1.65,11.65,narrow?3.5:4.65);
   text(d.body,.96,6.6,11.4,.45,22);
  }
  if(i===0&&members)text(members,8.4,4.9,4.0,1.5,18,{align:'right',fill:{color:C.white}});
  const sources=manifest.filter(r=>r.slide===i+1).map(r=>`${r.file} :: ${Array.isArray(r.key)?r.key.join('.'):r.key} [${r.category}]`).join('\n');
  s.addNotes(`말할 시간: ${d.seconds}초\n말할 문장과 범위: ${d.notes}\n승인 개요 번호: ${d.outline}\n수치 출처와 범주:\n${sources||'승인 개요의 장별 출처와 범위 참조'}\n${d.outline===4?'HAL은 하드웨어 연결부. 스택 계산은 별도 모델이며 독립 SIL을 결합 폐루프로 해석하지 않는다.':''}\n${d.outline===5?'저장소 https://github.com/ycpark06/hbm-stacking-edu-sim\nPages https://ycpark06.github.io/hbm-stacking-edu-sim/web/\n기존 개요 5·6장을 합쳤다. 영상에서 본 저장소로 연결한다.':''}`);
 }
 for(const b of boxes)if(b.x<0||b.y<0||b.x+b.w>13.334||b.y+b.h>7.501)throw Error('텍스트 경계 초과');
 await p.writeFile({fileName:output});
 const zip=await JSZip.loadAsync(fs.readFileSync(output));
 for(const f of Object.keys(zip.files).filter(f=>/^ppt\/theme\/theme.*\.xml$/.test(f))){let xml=await zip.file(f).async('string');xml=xml.replace(/<a:ea typeface="[^"]*"\s*\/>/g,'<a:ea typeface="Pretendard"/>').replace(/<a:font script="Hang" typeface="[^"]*"\s*\/>/g,'<a:font script="Hang" typeface="Pretendard"/>');zip.file(f,xml);}
 fs.writeFileSync(output,await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE'}));
 // Never persist private names or IDs in build diagnostics.
 if(!coverPath)fs.writeFileSync(path.join(__dirname,'layout_manifest.json'),JSON.stringify(boxes,null,2)+'\n');
 console.log(JSON.stringify({slides:D.slides.length,seconds:D.slides.reduce((a,s)=>a+s.seconds,0),public:!coverPath}));
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});
