"""Visual V2 experiment views; abstract outputs never enter measured data."""
import math
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from engine import compare, scale_network, cost_example

COLORS = {'RIP':'#f6ae73','OSPF':'#78dcc6'}


@st.cache_data(show_spinner=False)
def runs(n, delay, interval, horizon):
    return compare(scale_network(n), horizon=horizon,
                   rip_trigger_delay=delay, rip_periodic_interval=interval)


def settings():
    with st.expander('Model settings · abstract ticks, not seconds'):
        a,b,c=st.columns(3)
        delay=a.slider('RIP trigger delay',1,8,3,key='model_delay')
        interval=b.slider('RIP periodic interval',6,24,12,key='model_interval')
        horizon=c.slider('Observation window',24,80,48,step=4,key='model_horizon')
        st.caption('Immediate endpoint detection. OSPF floods one link per tick; no Hello/dead timers, acknowledgements or retransmissions. RIP uses simplified triggered full-vector advertisements and poison reverse. Counts are events, not bytes or CPU.')
    return delay,interval,horizon


def network_chart(network, point, color):
    positions={'R1':(0,0),'R2':(1,1),'R4':(2,0),'R3':(.6,-1),'R5':(1.4,-1)}
    if len(network.nodes)!=5:
        positions={r:(math.cos(2*math.pi*i/len(network.nodes)),math.sin(2*math.pi*i/len(network.nodes))) for i,r in enumerate(network.nodes)}
    fig=go.Figure()
    walked={tuple(sorted((a,b))) for a,b in zip(point['path_nodes'],point['path_nodes'][1:])}
    failed=tuple(sorted(network.failed_edge))
    for edge in network.edges:
        x,y=positions[edge.a],positions[edge.b]
        bad=edge.key==failed
        active=edge.key in walked
        fig.add_scatter(x=[x[0],y[0]],y=[x[1],y[1]],mode='lines',
            line=dict(color='#ed7a8a' if bad else color if active else '#334b61',width=4 if active else 2,dash='dash' if bad else 'solid'),
            hovertemplate=f'{edge.a} ↔ {edge.b}<br>'+('LINK DOWN' if bad else 'Link available')+'<extra></extra>',showlegend=False)
    states={r['router']:r for r in point['router_states']}
    fig.add_scatter(x=[positions[r][0] for r in network.nodes],y=[positions[r][1] for r in network.nodes],
        text=network.nodes,mode='markers+text',textposition='middle center',textfont=dict(color='#f1f8fc',size=12),
        marker=dict(size=43,color='#1c3547',line=dict(color=color,width=2)),
        customdata=[[states[r]['next_hop'] or 'Unreachable',str(states[r]['metric']) if states[r]['metric'] is not None else ('Yes' if states[r]['failure_known'] else 'No')] for r in network.nodes],
        hovertemplate='%{text}<br>Next hop to '+network.destination+': %{customdata[0]}<br>RIP metric / OSPF failure known: %{customdata[1]}<extra></extra>',showlegend=False)
    fig.update_layout(height=350,xaxis=dict(visible=False,range=[-.3,2.3]),yaxis=dict(visible=False,range=[-1.4,1.4]),margin=dict(l=15,r=15,t=15,b=15),dragmode=False)
    return fig


def playback(pair):
    """Browser-only playback of computed forwarding walks, never synthetic measurements."""
    traces={p:[{k:r[k] for k in ('tick','path','delivered')} for r in record['timeline']] for p,record in pair.items()}
    template='''<html><meta name="viewport" content="width=device-width"><style>body{margin:0;background:#111e2c;color:#d7e6ee;font:13px Arial}section{border:1px solid #304459;border-radius:12px;padding:16px}button,select{background:#21394a;color:#dbf1eb;border:1px solid #497064;border-radius:7px;padding:8px;cursor:pointer}button:hover{transform:translateY(-2px)}header{display:flex;gap:8px;align-items:center}small{margin-left:auto;color:#829fb1;font-size:10px}svg{width:100%;height:155px}circle{fill:#1c3649;stroke:#6b9b9b}text{fill:#d7e6ee;text-anchor:middle;font-size:13px}#line{fill:none;stroke:#78dcc6;stroke-width:4;stroke-dasharray:10 8;animation:flow 1s linear infinite}@keyframes flow{to{stroke-dashoffset:-36}}p{margin:5px 0;color:#a6c2cf}input{width:100%;accent-color:#78dcc6}@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style><section><header><button id="play">▶ Play</button><button id="reset">↺ Reset</button><select id="proto" aria-label="Playback protocol"><option>RIP</option><option>OSPF</option></select><small>MODEL PLAYBACK</small></header><svg viewBox="0 0 600 180"><path d="M60 90L260 30L540 90M60 90L220 155H380L540 90" fill="none" stroke="#344f62" stroke-width="2"/><path d="M260 30L540 90" stroke="#ed7a8a" stroke-dasharray="5 6"/><path id="line"/><g><circle cx="60" cy="90" r="21"/><text x="60" y="95">R1</text><circle cx="260" cy="30" r="21"/><text x="260" y="35">R2</text><circle cx="220" cy="155" r="21"/><text x="220" y="160">R3</text><circle cx="380" cy="155" r="21"/><text x="380" y="160">R5</text><circle cx="540" cy="90" r="21"/><text x="540" y="95">R4</text></g></svg><input id="tick" type="range" min="0" value="0" aria-label="Playback tick"><p id="label" aria-live="polite"></p></section><script>const traces=__DATA__;const $=id=>document.getElementById(id);let timer=null;const pos={R1:[60,90],R2:[260,30],R3:[220,155],R5:[380,155],R4:[540,90]};function stop(){clearInterval(timer);timer=null;$('play').textContent='▶ Play'}function draw(){let trace=traces[$('proto').value];$('tick').max=trace.length-1;let r=trace[+$('tick').value];$('label').textContent='Tick '+r.tick+' · '+(r.delivered?'Delivered':'Dropped')+' · '+r.path;$('line').setAttribute('d',r.path.split(' → ').map((n,i)=>(i?'L':'M')+pos[n].join(' ')).join(' '));$('line').style.stroke=$('proto').value==='RIP'?'#f6ae73':'#78dcc6'}$('play').onclick=()=>{if(timer){stop();return}if(+$('tick').value===+$('tick').max)$('tick').value=0;$('play').textContent='Ⅱ Pause';timer=setInterval(()=>{if(+$('tick').value>=+$('tick').max){stop();return}$('tick').value=+$('tick').value+1;draw()},600)};$('reset').onclick=()=>{stop();$('tick').value=0;draw()};$('proto').onchange=draw;$('tick').oninput=draw;draw();</script></html>'''
    components.html(template.replace('__DATA__',json.dumps(traces)),height=310,scrolling=False)


def failure_lab(style, section, parameters):
    section('MODEL / FAILURE LAB','Watch recovery happen.','Same failed link. Independent router knowledge. One probe per abstract tick.')
    delay,interval,horizon=parameters
    pair=runs(5,delay,interval,horizon)
    columns=st.columns(4)
    for col,(p,key,label) in zip(columns,[('RIP','convergence_ticks','RIP stable route'),('OSPF','convergence_ticks','OSPF stable route'),('RIP','lost_probes','RIP failed probes'),('OSPF','lost_probes','OSPF failed probes')]):
        value=pair[p]['summary'][key]
        col.metric(label,('Not stable' if value is None else str(value))+((' tick' if value==1 else ' ticks') if key=='convergence_ticks' and value is not None else ''))
    playback(pair)
    with st.expander('Inspect a tick · forwarding diagnosis'):
        protocol=st.radio('Inspect routing state',['RIP','OSPF'],horizontal=True,key='failure_protocol')
        if st.session_state.get('failure_tick',0)>horizon:st.session_state.failure_tick=0
        tick=st.slider('Inspect model tick',0,horizon,key='failure_tick')
        point=pair[protocol]['timeline'][tick]
        a,b=st.columns([1.6,1])
        with a:
            fig=style(network_chart(pair[protocol]['network'],point,COLORS[protocol]))
            fig.update_layout(height=350)
            st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False},key='failure_network')
        with b:
            (st.success if point['delivered'] else st.error)('Probe delivered' if point['delivered'] else 'Probe dropped')
            st.code(point['path'],language='text')
            st.caption(point['reason'])
            st.metric('Updates sent so far',point['control_messages'])
            st.caption(f"{point['recalculations']} routing calculation events")
    a,b=st.columns(2)
    for col,field,title in [(a,'delivered','Probe delivery'),(b,'control_messages','Cumulative update transmissions')]:
        fig=go.Figure()
        for p,record in pair.items():
            trace=record['timeline']
            fig.add_scatter(x=[r['tick'] for r in trace],y=[int(r[field]) for r in trace],name=p,mode='lines',line=dict(color=COLORS[p],width=3,shape='hv',dash='dash' if p=='RIP' else 'solid'),hovertemplate=p+' · tick %{x}<br>%{y}<extra></extra>')
        fig.add_vline(x=tick,line_color='#8da2b7',line_dash='dot')
        fig.update_xaxes(title='Abstract ticks')
        if field=='delivered':fig.update_yaxes(tickvals=[0,1],ticktext=['Drop','Delivered'],range=[-.1,1.15])
        with col:
            st.markdown('**'+title+'**')
            st.plotly_chart(style(fig),use_container_width=True,key='failure_'+field)
    with st.expander('Per-router state at this tick'):
        st.dataframe(pd.DataFrame(point['router_states']),hide_index=True,use_container_width=True)
        st.caption('RIP metric 16 = unreachable. OSPF failure-known indicates receipt of the link-down announcement.')
    rows=[{'source':'ABSTRACT_MODEL_NOT_PACKET_TRACER','protocol':p,**{k:v for k,v in row.items() if k not in ('path_nodes','router_states')}} for p,r in pair.items() for row in r['timeline']]
    st.download_button('↓ Download model trace',pd.DataFrame(rows).to_csv(index=False),file_name='ABSTRACT_MODEL_trace.csv')
    st.caption('Stable route = final delivered source path retained through the remaining window; not global convergence. Update counts omit OSPF background traffic and do not establish real overhead.')


def scaling_lab(style, section, parameters):
    section('MODEL / SCALABILITY','Grow the network.','Ring-and-shortcut networks with a surviving backup route.')
    sizes=st.multiselect('Router counts',[5,8,12,16,20,28,36],default=[5,8,12,16,20],key='scale_sizes')
    if not sizes:
        st.info('Choose at least one network size.');return
    rows=[r['summary'] for size in sorted(sizes) for r in runs(size,*parameters).values()]
    data=pd.DataFrame(rows)
    a,b=st.columns(2)
    for i,(field,title,units) in enumerate([('convergence_ticks','Source route stabilization','Abstract ticks'),('lost_probes','Failed probes','One probe / tick'),('control_messages','Update transmissions','Incomplete model count'),('routing_recalculations','Routing calculations','Events, not CPU')]):
        fig=go.Figure()
        for p,color in COLORS.items():
            r=data[data.protocol==p]
            fig.add_scatter(x=r.routers,y=r[field],mode='lines+markers',name=p,line=dict(color=color,width=3,dash='dash' if p=='RIP' else 'solid'),marker=dict(size=9),hovertemplate=p+' · %{x} routers<br>%{y}<extra></extra>')
        fig.update_xaxes(title='Routers');fig.update_yaxes(title=units)
        with (a if i%2==0 else b):
            st.markdown('**'+title+'**');st.plotly_chart(style(fig),use_container_width=True,key='scaling_'+field)
    with st.expander('Inspect scenarios and export'):
        st.dataframe(data[['routers','protocol','failed_link','convergence_ticks','lost_probes','control_messages','final_path']],hide_index=True)
        st.download_button('↓ Download scaling results',data.to_csv(index=False),file_name='ABSTRACT_MODEL_scalability.csv')
    st.caption('Descriptive model curves. Topology shape and failed-link position change with size; this does not isolate size as a cause. Counts omit real protocol traffic.')


def decisions_lab(style,section,parameters):
    section('MODEL / ROUTING DECISIONS','Fewer hops or lower cost?','A separate weighted-path experiment: upper links cost 8, lower links cost 1.')
    routes=cost_example()
    a,b=st.columns(2)
    for col,p in [(a,'RIP'),(b,'OSPF')]:
        with col:
            st.metric(p+' path',' → '.join(routes[p]))
            st.caption('2 hops · configured cost 16' if p=='RIP' else '3 hops · configured cost 3')
    fig=go.Figure()
    fig.add_bar(name='Hops',x=['RIP','OSPF'],y=[2,3],marker_color='#78dcc6')
    fig.add_bar(name='Configured path cost',x=['RIP','OSPF'],y=[16,3],marker_color='#f6ae73')
    fig.update_layout(barmode='group');st.plotly_chart(style(fig),use_container_width=True,key='decision_cost')
    a,b=st.columns([1,2])
    size=a.select_slider('Network size',[5,8,12,16,20,28,36],value=12,key='decision_size')
    priority=b.selectbox('Compare priority',['Failure recovery','Route-cost control','Simple small network','Control events'],key='decision_priority')
    pair=runs(size,*parameters)
    if priority=='Route-cost control':message='OSPF supports configurable link costs; RIP uses hop count.'
    elif priority=='Simple small network':message='RIP is a candidate for small, simple networks; evaluate its 15-hop limit and recovery behavior.' if size<=8 else 'Evaluate OSPF for this larger design; topology diameter and operational needs also matter.'
    elif priority=='Control events':
        message=f"Model events: RIP {pair['RIP']['summary']['control_messages']}, OSPF {pair['OSPF']['summary']['control_messages']}. Omitted OSPF traffic prevents a real-overhead recommendation."
    else:
        values={p:r['summary']['convergence_ticks'] for p,r in pair.items()}
        message=f"Source route stabilization: RIP {values['RIP']} ticks, OSPF {values['OSPF']} ticks under these model settings. Validate recovery with timed Cisco trials."
    st.info(message)
    st.caption('Decision support for this experiment, not a production benchmark. Recorded steady-state Cisco probes cannot rank recovery speed.')
