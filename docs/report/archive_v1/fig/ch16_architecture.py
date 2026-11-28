"""README 2절 아키텍처를 보고서 그림으로 표현한다(모델 수치 없음)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
fonts={f.name for f in font_manager.fontManager.ttflist}
plt.rcParams['font.family']=next((f for f in ['Noto Sans CJK KR','Apple SD Gothic Neo','AppleGothic'] if f in fonts),'sans-serif')
fig,ax=plt.subplots(figsize=(10,6));ax.set(xlim=(0,10),ylim=(0,7));ax.axis('off')
def box(x,y,t):ax.text(x,y,t,ha='center',va='center',fontsize=10,bbox=dict(boxstyle='round,pad=.6',fc='#e8eef5',ec='#2b5c8a'))
def arr(a,b):ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color='#456'))
box(5,6.4,'공통 C 제어기 · firmware/src')
for x,t in [(1.5,'PC HAL\ngolden · 고정 입력'),(5,'MCU HAL\nSTM32H743 · .bin'),(8.5,'wasm HAL\n.js + .wasm')]:box(x,5,t);arr((5,6.1),(x,5.5))
box(2.4,3.5,'JS 플랜트 + wasm\n독립 SIL · 고장 주입');arr((8.3,4.5),(3.6,3.9))
box(7.6,3.5,'sim/stack.js\n열 · 휨 · 충전 · 정렬')
box(5,2.1,'ES module Worker');arr((2.4,3),(4.1,2.4));arr((7.6,3),(5.9,2.4))
box(5,.8,'HMI · Canvas 그래프 · three.js / GLB');arr((5,1.8),(5,1.2))
fig.text(.5,.02,'GitHub Actions: Node 24 테스트 → 사이트 조립 → GitHub Pages',ha='center',fontsize=10)
fig.savefig(Path(__file__).with_suffix('.png'),dpi=180,bbox_inches='tight')
