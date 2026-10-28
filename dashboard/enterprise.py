"""Enterprise WAN experiments: explicit synthetic costs, matched probes and failures."""
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from engine import Edge, Network, compare, shortest_path

SITES={'R1':'HQ gateway','R2':'Legacy WAN','R3':'Core west','R4':'Branch west','R5':'Core central','R6':'Branch central','R7':'Legacy transit','R8':'Core east','R9':'Branch east','R10':'DR transit','R11':'Core backup','R12':'Data center'}
POSITIONS={'R1':(90,240),'R2':(280,80),'R7':(510,60),'R10':(760,80),'R3':(280,225),'R5':(510,205),'R8':(760,225),'R4':(280,400),'R6':(510,420),'R9':(760,400),'R11':(640,310),'R12':(990,240)}
LINKS=[('R1','R2',12),('R2','R12',12),('R1','R3',2),('R3','R5',2),('R5','R8',2),('R8','R12',2),('R1','R4',3),('R4','R6',3),('R6','R9',3),('R9','R12',3),('R3','R4',2),('R5','R6',2),('R8','R9',2),('R2','R7',8),('R7','R10',8),('R10','R9',8),('R5','R11',2),('R11','R8',2)]


def enterprise_network(weighted=True,failed=('R2','R12')):
    return Network([Edge(a,b,c if weighted else 1) for a,b,c in LINKS],'R1','R12',failed,'12-router enterprise WAN · '+('configured WAN costs' if weighted else 'equal costs'))


def path_cost(network,path):
    adj=network.adjacency()
    return sum(adj[a][b] for a,b in zip(path,path[1:])) if path else None


@st.cache_data(show_spinner=False)
def experiment(weighted,failed,parameters):
    delay,interval,horizon=parameters
    return compare(enterprise_network(weighted,failed),horizon=horizon,rip_trigger_delay=delay,rip_periodic_interval=interval)


def selectable_paths(network):
    """Offer distinct preferred and branch routes, using actual topology edges."""
    paths={p+' preferred route':shortest_path(network.adjacency(),'R1','R12',p) for p in ('RIP','OSPF')}
    paths['Branch WAN route']=['R1','R4','R6','R9','R12']
    paths['DR transit route']=['R1','R2','R7','R10','R9','R12']
    paths['Core backup route']=['R1','R3','R5','R11','R8','R12']
    return paths


def diagram(pair,baseline,start_failure=False):
    net=pair['RIP']['network']
    payload={'startFailure':start_failure,'positions':POSITIONS,'sites':SITES,'edges':[[e.a,e.b,e.cost] for e in net.edges],'failed':list(net.failed_edge),'baseline':baseline,
             'traces':{p:[{k:r[k] for k in ('tick','path_nodes','delivered','reason')} for r in record['timeline']] for p,record in pair.items()}}
    page='''<!doctype html><html><meta name="viewport" content="width=device-width"><style>*{box-sizing:border-box}body{margin:0;font:13px Arial;color:#d8e7f1;background:#101e2c}.panel{border:1px solid #34495c;border-radius:15px;padding:15px}header{display:flex;gap:8px;align-items:center;flex-wrap:wrap}button,select{background:#213849;color:#d9f4ec;border:1px solid #496677;border-radius:7px;padding:9px;cursor:pointer;transition:.2s}button:hover{transform:translateY(-3px);border-color:#78dcc6}small{margin-left:auto;color:#90a9bd;font-size:10px}svg{width:100%;height:410px;background:radial-gradient(ellipse,#1a3041,#101e2c)}.edge{stroke:#3c5369;stroke-width:2;fill:none}.router circle{fill:#1c3548;stroke:#6b91a9;stroke-width:2;transition:.2s}.router:hover circle{fill:#36605e;stroke:#78dcc6;filter:drop-shadow(0 0 6px #78dcc6)}.router{cursor:pointer}text{fill:#deedf6;text-anchor:middle;font:12px Arial}.cost{fill:#8faabc;font-size:10px}.label{fill:#8faabc;font-size:10px}.route{fill:none;stroke-width:5;stroke-dasharray:12 8;animation:flow 1s linear infinite}input{width:100%;accent-color:#78dcc6}.paths{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:10px 0}.paths div{border:1px solid #30495e;border-radius:8px;padding:12px;line-height:1.6}.orange{color:#f6ae73}.mint{color:#78dcc6}#inspect{color:#8faabc;font-size:11px;margin-top:10px}@keyframes flow{to{stroke-dashoffset:-40}}@media(max-width:650px){svg{height:300px}.paths{grid-template-columns:1fr}small{display:none}}@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}</style><div class="panel"><header><button id="play">▶ Play failure</button><button id="reset">↺ Baseline</button><select id="show" aria-label="Visible route"><option>Both protocols</option><option>RIP</option><option>OSPF</option></select><small>ENTERPRISE WAN / MODEL ONLY</small></header><svg viewBox="0 0 1080 480" aria-label="Twelve router enterprise WAN"><g id="edges"></g><g id="routes"></g><g id="nodes"></g></svg><input id="tick" aria-label="Enterprise playback tick" type="range" min="-1" value="-1"><div id="status">Baseline</div><div class="paths"><div class="orange" id="rip"></div><div class="mint" id="ospf"></div></div><div id="inspect">Hover over links for costs. Click a router for its role.</div></div><script>const D=__DATA__,$=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';let timer=null;function el(tag,attrs,parent){let n=document.createElementNS(NS,tag);for(let k in attrs)n.setAttribute(k,attrs[k]);parent.appendChild(n);return n}function stop(){clearInterval(timer);timer=null;$('play').textContent='▶ Play failure'}function draw(){let t=+$('tick').value;let edgeRoot=$('edges');edgeRoot.replaceChildren();D.edges.forEach(([a,b,c])=>{let p=D.positions[a],q=D.positions[b],bad=t>=0&&D.failed.includes(a)&&D.failed.includes(b);let l=el('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],class:'edge',style:bad?'stroke:#f27e8d;stroke-dasharray:5 7':''},edgeRoot);el('title',{},l).textContent=a+' ↔ '+b+' · configured cost '+c+(bad?' · DOWN':'');let txt=el('text',{x:(p[0]+q[0])/2,y:(p[1]+q[1])/2-6,class:'cost'},edgeRoot);txt.textContent=c});$('routes').replaceChildren();['RIP','OSPF'].forEach(p=>{let r=t<0?{path_nodes:D.baseline[p],delivered:true,reason:'Baseline route'}:D.traces[p][t];let visible=$('show').value==='Both protocols'||$('show').value===p;if(visible){let path=r.path_nodes.map((n,i)=>(i?'L':'M')+D.positions[n].join(' ')).join(' ');el('path',{d:path,class:'route',stroke:p==='RIP'?'#f6ae73':'#78dcc6',opacity:.85,style:p==='RIP'?'stroke-width:8':'stroke-width:4'},$('routes'))}$(p.toLowerCase()).textContent=p+' · '+(r.delivered?'Delivered':'Dropped')+' · '+r.path_nodes.join(' → ')});$('status').textContent=t<0?'BASELINE · ALL LINKS AVAILABLE':'MODEL TICK '+t+' · '+D.failed.join('–')+' DOWN'}Object.entries(D.positions).forEach(([n,p])=>{let g=el('g',{class:'router',tabindex:0,role:'button','aria-label':n+' '+D.sites[n]},$('nodes'));el('circle',{cx:p[0],cy:p[1],r:22},g);el('text',{x:p[0],y:p[1]+4},g).textContent=n;el('text',{x:p[0],y:p[1]+39,class:'label'},g).textContent=D.sites[n];g.onclick=()=>$('inspect').textContent=n+' / '+D.sites[n]+' · '+D.edges.filter(e=>e[0]===n||e[1]===n).map(e=>(e[0]===n?e[1]:e[0])+' (cost '+e[2]+')').join(' · ');g.onkeydown=e=>{if(e.key==='Enter')g.onclick()}});$('tick').max=D.traces.RIP.length-1;$('tick').oninput=()=>{stop();draw()};$('show').onchange=draw;$('reset').onclick=()=>{stop();$('tick').value=-1;draw()};$('play').onclick=()=>{if(timer){stop();return}if(+$('tick').value>=+$('tick').max)$('tick').value=-1;$('play').textContent='Ⅱ Pause';timer=setInterval(()=>{if(+$('tick').value>=+$('tick').max){stop();return}$('tick').value=+$('tick').value+1;draw()},650)};draw();</script></html>'''
    page=page.replace('draw();</script>',"draw();if(D.startFailure){$('play').click()}</script>")
    components.html(page.replace('__DATA__',json.dumps(payload)),height=660,scrolling=False)


def enterprise_lab(style,section,parameters):
    section('ENTERPRISE / PERFORMANCE ANALYSIS','Same destination. Different decisions.','12 routers · 18 WAN links · HQ, branch, core and data-center routes. Educational model; existing Cisco captures cover 5 routers.')
    a,b=st.columns(2)
    mode=a.selectbox('Controlled experiment',['WAN costs · route efficiency','Equal costs · matched failure'],key='enterprise_mode')
    weighted=mode.startswith('WAN')
    choices=selectable_paths(enterprise_network(weighted))
    route_name=b.selectbox('Select path to disrupt',list(choices)+['Any WAN link'],key='enterprise_path')
    chosen_path=choices.get(route_name)
    edge_options=list(zip(chosen_path,chosen_path[1:])) if chosen_path else [(a,b) for a,b,_ in LINKS]
    options=['–'.join(edge) for edge in edge_options]
    # Prefer the remote link on the default legacy path, so propagation is visible.
    link=st.selectbox('Select the link to fail on this path',options,index=min(1,len(options)-1),key='enterprise_link')
    if chosen_path:
        st.code(' → '.join(chosen_path),language='text')
    apply=st.button('↯ Fail selected path',key='enterprise_apply_failure',type='primary')
    st.caption('A route becomes unavailable when one of its links fails. This control breaks the selected link; the other links stay available for alternate routing. Charts show the selected failure scenario; press the button to play it.')
    failed=tuple(link.split('–'))
    pair=experiment(weighted,failed,parameters)
    network=pair['RIP']['network']
    baseline={p:shortest_path(network.adjacency(),'R1','R12',p) for p in ('RIP','OSPF')}
    cols=st.columns(4)
    cols[0].metric('RIP baseline hops',len(baseline['RIP'])-1)
    cols[1].metric('OSPF baseline hops',len(baseline['OSPF'])-1)
    cols[2].metric('RIP baseline path cost',path_cost(network,baseline['RIP']))
    cols[3].metric('OSPF baseline path cost',path_cost(network,baseline['OSPF']))
    diagram(pair,baseline,start_failure=apply)
    if apply:st.success(f'{link} failed in the model. Playback now follows the actual recomputed forwarding trace for both protocols.')
    if weighted:
        st.info('RIP chooses the 2-hop legacy WAN (cost 24). OSPF chooses the 4-hop core path (cost 8). Costs are configured values, not measured latency. A failed link can affect one selected route and leave the other unaffected.')
    else:
        st.info('All links now cost 1. Both protocols start on the same shortest path. Use R2–R12 failure to compare matched recovery behavior under the same costs and probe window.')
    section('PERFORMANCE / OBSERVABLE OUTCOMES','Compare the disruption.','One source-to-destination probe per abstract tick. Hover to inspect exact values.')
    rows=[r['summary'] for r in pair.values()]
    summary=pd.DataFrame(rows)
    a,b=st.columns(2)
    for col,field,title in [(a,'delivered','Service availability'),(b,'control_messages','Cumulative update events')]:
        fig=go.Figure()
        for p,r in pair.items():
            trace=r['timeline']
            fig.add_scatter(x=[x['tick'] for x in trace],y=[int(x[field]) for x in trace],name=p,mode='lines',line=dict(color='#f6ae73' if p=='RIP' else '#78dcc6',width=3,shape='hv',dash='dash' if p=='RIP' else 'solid'),hovertemplate=p+' · tick %{x}<br>%{y}<extra></extra>')
        fig.update_xaxes(title='Abstract model ticks')
        if field=='delivered':fig.update_yaxes(tickvals=[0,1],ticktext=['Dropped','Delivered'],range=[-.1,1.15])
        with col:
            st.markdown('**'+title+'**');st.plotly_chart(style(fig),use_container_width=True,key='enterprise_'+field)
    a,b=st.columns(2)
    for col,p in [(a,'RIP'),(b,'OSPF')]:
        r=pair[p]['summary']
        with col:
            st.metric(p+' source-route stabilization',str(r['convergence_ticks'])+' ticks' if r['convergence_ticks'] is not None else 'Not stable in window')
            st.caption(f"{r['lost_probes']}/{r['probe_count']} failed probes · {r['routing_recalculations']} routing calculation events")
            st.code(r['final_path'] or 'No delivered final route',language='text')
    with st.expander('Why this is performance analysis · method and limits'):
        st.markdown('**Route efficiency:** compare hops and configured path cost. **Service continuity:** inspect drops during failure, not just successful pings afterward. **Recovery:** measure source-path stabilization within the stated observation window. **Control activity:** count modeled updates and recalculations. **Scale:** compare the Scalability tab. No CPU, throughput or real-time latency is measured. OSPF counts omit Hello/acknowledgement traffic, so they cannot establish total real overhead. Model stabilization is not global convergence.')
        st.dataframe(summary[['protocol','convergence_ticks','lost_probes','probe_count','delivery_percent','control_messages','routing_recalculations','final_path']],hide_index=True)
    summary['source']='ABSTRACT_ENTERPRISE_MODEL_NOT_CISCO'
    st.download_button('↓ Export enterprise model results',summary.to_csv(index=False),file_name='ABSTRACT_ENTERPRISE_MODEL.csv')

