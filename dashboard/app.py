"""Visual routing performance dashboard with local Cisco integration."""
from __future__ import annotations
import html
import subprocess
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import COLUMNS,validate_records
st.set_page_config(page_title='Performance Analysis | RIP vs OSPF',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
st.markdown('<style>'+(ROOT/'dashboard/theme.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)
COLORS={'RIP':'#f6ae73','OSPF':'#78dcc6'}
LABELS={'baseline':'Baseline','failover':'Link failure','recovery':'Restored','cost_demo':'Cost demo'}

from measurements import read_data
from labs import settings, failure_lab, scaling_lab, decisions_lab
from enterprise import enterprise_lab

def style_chart(fig):
    fig.update_layout(height=310,margin=dict(l=10,r=10,t=25,b=10),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='Arial',color='#b9cada',size=12),legend=dict(orientation='h',y=1.17,x=0),xaxis=dict(showgrid=False,zeroline=False),yaxis=dict(gridcolor='#28394b',zeroline=False),hoverlabel=dict(bgcolor='#182638',font_color='#fff'),bargap=.4,transition=dict(duration=450))
    return fig

def section(kicker,title,detail=''):
    st.markdown(f'<div class="section-head"><span>{kicker}</span><h3>{title}</h3><p>{detail}</p></div>',unsafe_allow_html=True)

data=read_data(ROOT/'data/measured_results.csv')
st.markdown('''<div class="masthead"><div class="brand"><b>◈</b> ROUTE<span>LAB</span><i>NETWORK SYSTEMS / ENTERPRISE</i></div><div class="status"><em></em> CISCO EXPERIMENTS SAVED</div></div><div class="hero"><div class="eyebrow">COMPUTER NETWORKS · PROTOCOL BENCHMARK</div><h1>Performance analysis<span>RIP <i>versus</i> OSPF.</span></h1><p>One network. Two routing strategies. See the difference.</p><div class="hero-orbit">◎</div></div>''',unsafe_allow_html=True)
enterprise,failure,lab,scaling,decisions,performance,cisco=st.tabs(['◈ Enterprise WAN','↯ Failure Lab','◈ Routing Lab','↗ Scalability','◇ Decisions','▥ Cisco Results','↗ Cisco Workspace'])
with failure:
    parameters=settings()
    failure_lab(style_chart,section,parameters)
with enterprise:
    enterprise_lab(style_chart,section,parameters)
with scaling:
    scaling_lab(style_chart,section,parameters)
with decisions:
    decisions_lab(style_chart,section,parameters)
with lab:
    st.markdown('''<div class="stat-strip"><div><small>TOPOLOGY</small><strong>05 <span>routers</span></strong><b>02 LANs · 09 links</b></div><div><small>BACKUP PATH</small><strong>03 <span>hops</span></strong><b>Verified in Packet Tracer</b></div><div><small>SETTLED DELIVERY</small><strong>100<span>%</span></strong><b>4/4 packets per probe</b></div><div><small>CISCO CHECKS</small><strong>05 <span>runs</span></strong><b>Single verification per state</b></div></div>''',unsafe_allow_html=True)
    section('01 / INTERACTIVE NETWORK','Follow the packet.','Switch protocols, break the upper link, or inspect a router.')
    components.html((ROOT/'dashboard/topology.html').read_text(encoding='utf-8'),height=750,scrolling=False)
    st.markdown('<div class="footnote"><span class="mint">●</span> Animated route model · Recorded Cisco results in Performance · No live telemetry connection</div>',unsafe_allow_html=True)
with performance:
    section('02 / MEASURED PERFORMANCE','Evidence, at a glance.','Cisco Packet Tracer observations. Hover over a graph to inspect the probe.')
    with st.expander('Import your next experiment'):
        uploaded=st.file_uploader('Results CSV',type='csv',key='results_upload')
        st.download_button('Download blank worksheet',(ROOT/'data/results_template.csv').read_bytes(),file_name='results_template.csv',mime='text/csv')
        st.download_button('Download V2 measurement sheet',(ROOT/'data/MEASURED_PACKET_TRACER_BLANK.csv').read_bytes(),file_name='MEASURED_PACKET_TRACER_BLANK.csv',mime='text/csv')
        st.caption('Both CSV formats accepted. V2 milliseconds convert to seconds; capture methods and network sizes stay separate.')
    if uploaded is not None:
        try: data=read_data(uploaded)
        except (ValueError,pd.errors.ParserError,UnicodeDecodeError,OverflowError) as exc:
            st.error(str(exc));st.stop()
    if data.router_count.nunique()>1:
        count=st.selectbox('Measured network size',sorted(data.router_count.unique()),key='measured_size')
        data=data[data.router_count==count]
    st.caption('Recorded network: '+(', '.join(str(int(n)) for n in data.router_count.unique()) or 'none')+' routers')
    scenario=st.radio('Compare scenario',['All checks','Baseline','Link failure','Restored'],horizontal=True,key='performance_scenario')
    inverse={v:k for k,v in LABELS.items()}
    selected=data if scenario=='All checks' else data[data.experiment==inverse[scenario]]
    valid=selected[(selected.sent_packets>0)&selected.received_packets.notna()]
    left,right=st.columns([1.2,1])
    with left:
        with st.container(border=True):
            section('PACKET DELIVERY','Did the packets arrive?')
            if valid.empty: st.info('No packet probe recorded for this state.')
            else:
                grouped=valid.groupby(['protocol','experiment'],sort=False).agg(sent=('sent_packets','sum'),received=('received_packets','sum'),runs=('trial','size')).reset_index()
                fig=go.Figure()
                for protocol,color in COLORS.items():
                    rows=grouped[grouped.protocol==protocol]
                    fig.add_bar(name=protocol,x=rows.experiment.map(LABELS),y=100*rows.received/rows.sent,marker=dict(color=color,cornerradius=7),text=[f'{100*r.received/r.sent:.0f}%' for r in rows.itertuples()],textposition='outside',customdata=rows[['received','sent','runs']],hovertemplate=protocol+' · %{x}<br><b>%{y:.1f}% delivered</b><br>%{customdata[0]:.0f}/%{customdata[1]:.0f} packets<br>%{customdata[2]} probe(s)<extra></extra>')
                fig.update_layout(barmode='group',yaxis_range=[0,118])
                st.plotly_chart(style_chart(fig),use_container_width=True,config={'displayModeBar':False})
            st.caption('After routes settled. Does not measure interruption loss.')
    with right:
        with st.container(border=True):
            section('ROUTE LENGTH','How far did they travel?')
            fig=go.Figure()
            paths=selected.dropna(subset=['route_hops']).groupby(['protocol','experiment'],sort=False).route_hops.mean().reset_index()
            for protocol,color in COLORS.items():
                rows=paths[paths.protocol==protocol]
                fig.add_scatter(name=protocol,x=rows.experiment.map(LABELS),y=rows.route_hops,mode='lines+markers',line=dict(color=color,width=3,dash='dash' if protocol=='RIP' else 'solid'),marker=dict(size=16 if protocol=='RIP' else 9,line=dict(color='#102030',width=2)),hovertemplate=protocol+' · %{x}<br><b>%{y:g} inter-router hops</b><extra></extra>')
            fig.update_yaxes(dtick=1,range=[0,4])
            st.plotly_chart(style_chart(fig),use_container_width=True,config={'displayModeBar':False})
            st.caption('Router-to-router links. PCs and switches excluded.')
    timed=selected[selected.convergence_s.notna()]
    if timed.empty:
        st.markdown('<div class="empty-metric"><span>◷</span><div><b>Convergence timing</b><p>Add timed trials to unlock this comparison.</p></div><i>NOT MEASURED</i></div>',unsafe_allow_html=True)
    else:
        basis=st.selectbox('Timing basis',sorted(timed.measurement_basis.unique()),key='timing_basis')
        means=timed[timed.measurement_basis==basis].groupby(['protocol','experiment']).convergence_s.mean().reset_index()
        fig=go.Figure()
        for protocol,color in COLORS.items():
            rows=means[means.protocol==protocol]
            fig.add_bar(name=protocol,x=rows.experiment.map(LABELS),y=rows.convergence_s,marker_color=color,hovertemplate=protocol+'<br>%{x}: %{y:.3f} seconds<extra></extra>')
        fig.update_layout(barmode='group')
        st.plotly_chart(style_chart(fig),use_container_width=True)
        st.caption('Mean observed seconds. Timing bases stay separate.')
    section('OBSERVED ROUTES','The path tells the story.')
    for row in selected.itertuples():
        route=html.escape(str(row.route_path)).replace('-&gt;','→')
        hops=int(row.route_hops) if pd.notna(row.route_hops) else '—'
        st.markdown(f'<div class="route-row"><b style="color:{COLORS[row.protocol]}">{row.protocol}</b><span>{LABELS[row.experiment]}</span><strong>{route}</strong><i>{hops} hops</i></div>',unsafe_allow_html=True)
    st.download_button('↓ Export recorded results',data.to_csv(index=False),file_name='measured_results.csv',mime='text/csv')
    st.caption('Single verification runs. Repeat trials before drawing a performance conclusion.')
with cisco:
    section('03 / CISCO WORKSPACE','From diagram to device.','Open your actual network or inspect the recorded console evidence.')
    st.markdown('<div class="connection-note"><span>◈</span><div><b>Local Packet Tracer integration</b><p>Launch saved .pkt files + import recorded results. Animations do not control Cisco devices.</p></div></div>',unsafe_allow_html=True)
    tracer=Path('D:/Cisco Packet Tracer 9.0.1/bin/PacketTracer.exe')
    for column,protocol in zip(st.columns(2),('RIP','OSPF')):
        with column:
            with st.container(border=True):
                st.markdown(f'<div class="project-card"><small>CISCO PACKET TRACER</small><h2 style="color:{COLORS[protocol]}">{protocol}<span> experiment</span></h2><p>5 routers · 2 LANs · baseline + backup path</p></div>',unsafe_allow_html=True)
                file=ROOT/f'{protocol}_Experiment.pkt'
                if st.button(f'↗ Open {protocol} in Cisco',key=f'open_{protocol}',use_container_width=True,disabled=not(file.exists() and tracer.exists())):
                    try:
                        subprocess.Popen([str(tracer),str(file)],cwd=str(ROOT))
                        st.success(f'{protocol} experiment sent to Packet Tracer.')
                    except OSError as exc: st.error(f'Could not open Packet Tracer: {exc}')
                if file.exists(): st.download_button(f'↓ Download {protocol} .pkt',file.read_bytes(),file_name=file.name,key=f'download_{protocol}',use_container_width=True)
    section('CONSOLE EVIDENCE','Inspect the proof.')
    evidence=sorted((ROOT/'experiments/evidence').glob('*.txt'))
    chosen=st.selectbox('Recorded Cisco console',evidence,format_func=lambda p:p.stem.replace('_',' '),key='evidence_file')
    with st.expander('View console output'): st.code(chosen.read_text(encoding='utf-8'),language='text')
    with st.expander('Router configuration files'):
        protocol=st.selectbox('Configuration protocol',['RIP','OSPF'],key='config_protocol')
        router=st.selectbox('Router',['R1','R2','R3','R4','R5'],key='config_router')
        st.code((ROOT/'configs/paste_ready'/f'{router}_{protocol}_COMPLETE.txt').read_text(encoding='utf-8'),language='text')
    st.markdown('<div class="footnote">NEXT / Repeat 3 trials · Capture convergence timestamps · Separate cost demonstration</div>',unsafe_allow_html=True)
st.markdown('<div class="footer"><b>◈ ROUTELAB</b><span>DISTANCE VECTOR & LINK STATE ROUTING</span><i>RIPv2 / OSPFv2</i></div>',unsafe_allow_html=True)


