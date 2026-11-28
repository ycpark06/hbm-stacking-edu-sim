import {runStack} from '../../sim/stack.js';
import {runScenario} from '../../sim/scenarios.js';
import {loadController,forceSim} from '../../sim/plant.js';
import {recipeParams} from './recipe_limits.js';
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
self.onmessage=async({data})=>{
  const {id,params,recipe,scenario}=data;
  const send=(type,payload)=>self.postMessage({id,type,...payload});
  try {
    send('status',{message:scenario?`${scenario} 계산 중…`:'열·휨·충전·정렬 계산 중…'});
    let results,description='동일 레시피의 두 모드 비교';
    if(scenario){
      const s=runScenario(scenario,params);description=s.description;
      // Presets expose summaries. Obtain full unmodified histories for HMI
      // charts without changing the shared scenarios/model API.
      results=s.results.map(summary=>{
        const full=runStack(summary.recipe.mode,summary.recipe,params);
        return {...full,...summary,thermal:full.thermal,
          warpage:{...full.warpage,...summary.warpage},
          alignment:{...full.alignment,...summary.alignment}};
      });
    }
    else {const p=recipeParams(recipe,params);results=['TC-NCF','MR-MUF'].map(mode=>runStack(mode,{...recipe,mode},p));if(recipe.mode==='MR-MUF')results.reverse();}
    send('results',{results,description});
    const fw=await loadController();
    // Independent original ch10 SIL plant + wasm REFERENCE controller. The stack
    // thermal model uses ideal boundaries; do not imply this is coupled to it.
    const e=params.equipment_limits;
    const target=recipe?.bond_force_N??params.tcncf_process.bond_force.value;
    const ramp=recipe?.force_ramp_N_s??e.force_high_ramp_N_s.value;
    const sil=forceSim(fw,{F_target:target,
      t_end:target/ramp+e.sil_observation_tail_s.value,
      k_spring:(recipe?.low_range?e.force_low_spring_N_mm:e.force_high_spring_N_mm).value,
      ramp,approach:e.force_approach_mm_s.value,
      Ts:e.force_period_ms.value/1000});
    send('sil',{sil});
    // runStack has no incremental callback. Replay actual phase/layer events
    // after calculation, explicitly identified as an educational playback.
    const result=results.find(r=>r.accepted!==false),history=result?.thermal?.history;
    const events=history?history.filter((r,i)=>i===0||r.phase!==history[i-1].phase):
      Array.from({length:result?.recipe.layers??0},(_,i)=>({T:Array(i+1),phase:'적층',t:null}));
    for(const row of events){send('progress',{layer:row.T.length,phase:row.phase,t:row.t_s,recipe:result.recipe});await pause(180);}
    send('done',{});
  }catch(error){send('error',{message:error.message});}
};
