/* Recording-only DOM masking. No repository content is modified. */
(() => {
  const months='Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?';
  const patterns=[
    /\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}(?:[T\s]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?\b/g,
    new RegExp(`\\b(?:${months})\\.?\\s+\\d{1,2}(?:,?\\s+\\d{4})?\\b`,'gi'),
    new RegExp(`\\b\\d{1,2}\\s+(?:${months})\\.?(?:\\s+\\d{4})?\\b`,'gi'),
    /\b(?:\d+|a|an|one)\s+(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\s+ago\b/gi,
    /\b(?:yesterday|today|just now|last (?:week|month|year))\b/gi,
    /\d{4}년\s*\d{1,2}월\s*\d{1,2}일/g,
    /\d+\s*(?:초|분|시간|일|주|개월|년)\s*전/g,
    /\b(?:19|20)\d{2}\b/g
  ];
  function maskDateText(text){for(const pattern of patterns)text=text.replace(pattern,'▇▇');return text;}
  function maskDates(root=document.body){
    if(!root)return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    let node;while((node=walker.nextNode())){
      if(node.parentElement?.closest('script,style,noscript'))continue;
      const masked=maskDateText(node.nodeValue);if(masked!==node.nodeValue)node.nodeValue=masked;
    }
  }
  // Exposed for preparation and DOM-free regression tests.
  globalThis.recordingMask={maskDateText,maskDates};
  if(typeof document==='undefined')return;
  const install=()=>{
    const style=document.createElement('style');style.textContent='relative-time,time,time-ago,local-time,[datetime]{visibility:hidden!important}';document.head.append(style);
    maskDates();
    new MutationObserver(()=>maskDates()).observe(document.body,{subtree:true,childList:true,characterData:true});
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
