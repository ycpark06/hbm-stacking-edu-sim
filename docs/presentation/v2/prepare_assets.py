"""Optional refresh of source crops. Never opens cover JSON or reference PPTX files."""
import argparse,json
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
p=argparse.ArgumentParser();p.add_argument('--design-dir',type=Path,required=True);args=p.parse_args();A=HERE/'assets';A.mkdir(exist_ok=True)
records=[]
def crop(src,dst,box=None):
 im=Image.open(src).convert('RGB');im=im.crop(box) if box else im;im.save(A/(dst+'.png'))
 records.append(dict(asset=dst+'.png',source=str(src.relative_to(ROOT)) if src.is_relative_to(ROOT) else 'design_review/assets/'+src.name,crop=box))
L=ROOT/'media/stills/light';R=args.design_dir/'assets'
crop(L/'factory_light_mr_fill.png','factory',(280,140,980,800))
crop(L/'factory_light_tc.png','video',(280,140,980,800))
crop(L/'cad_light_exploded.png','exploded',(0,100,1030,850))
if (L/'cad_light_all.png').exists():crop(L/'cad_light_all.png','cad',(0,100,1030,850))
else:crop(ROOT/'media/stills/cad_overview.png','cad',(26,122,840,662))
crop(L/'github_repo.png','github',(190,365,535,895))
crop(L/'factory_light_tc.png','modes')
crop(R/'pr31_title.png','pr',(0,0,Image.open(R/'pr31_title.png').width,44))
for src,dst in [('hmi_alarms.png','alarms'),('hmi_s1_card1_layers1to4.png','results')]:crop(R/src,dst)
(HERE/'asset_sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
