"""Shared enterprise network comparisons."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import compare, shortest_path
from enterprise import enterprise_network, expanded_enterprise_network, path_cost
COLORS={'RIP':'#f6ae73','OSPF':'#78dcc6'}

@st.cache_data(show_spinner=False)
def runs(n, delay, interval, horizon):
    return compare(expanded_enterprise_network(n),horizon=horizon,rip_trigger_delay=delay,rip_periodic_interval=interval)

def settings():
    with st.expander('Simulation settings'):
        a,b,c=st.columns(3)
        delay=a.slider('RIP update wait (steps)',1,8,3,key='model_delay')
        interval=b.slider('RIP regular updates (steps)',6,24,12,key='model_interval')
        horizon=c.slider('Test length (steps)',24,80,48,step=4,key='model_horizon')
        st.caption('Immediate endpoint detection. OSPF floods one link per tick; no Hello/dead timers, acknowledgements or retransmissions. RIP uses simplified triggered full-vector advertisements and poison reverse. Counts are events, not bytes or CPU.')
    return delay,interval,horizon


def scaling_lab(style, section, parameters):
    section('MODEL / SCALABILITY','Grow the network.','Start with this same 12-router network, then add branches. R1, R12 and the failed R2–R12 link stay the same.')
    sizes=st.multiselect('Router counts',[12,16,20,28,36],default=[12,16,20],key='scale_sizes')
    if not sizes:
        st.info('Choose at least one network size.');return
    rows=[r['summary'] for size in sorted(sizes) for r in runs(size,*parameters).values()]
    data=pd.DataFrame(rows)
    a,b=st.columns(2)
    for i,(field,title,units) in enumerate([('convergence_ticks','Steps until the path works again','Simulation steps'),('lost_probes','Test packets lost','Packets'),('control_messages','Routing messages sent','Simplified count'),('routing_recalculations','Path updates checked','Checks, not CPU use')]):
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
    st.caption('The original 12 routers and 18 links stay in every network. Extra routers have two branch connections. Results depend on this design and the selected simulation settings.')


def decisions_lab(style,section,parameters):
    section('MODEL / ROUTING DECISIONS','Fewer hops or lower cost?','The same 12-router enterprise network. Compare the number of links and their total cost.')
    network=enterprise_network()
    routes={p:shortest_path(network.adjacency(),'R1','R12',p) for p in ('RIP','OSPF')}
    a,b=st.columns(2)
    for col,p in [(a,'RIP'),(b,'OSPF')]:
        with col:
            st.metric(p+' path',' → '.join(routes[p]))
            st.caption('2 links · total cost 24' if p=='RIP' else '4 links · total cost 8')
    fig=go.Figure()
    fig.add_bar(name='Number of links',x=['RIP','OSPF'],y=[2,4],marker_color='#78dcc6')
    fig.add_bar(name='Total link cost',x=['RIP','OSPF'],y=[24,8],marker_color='#f6ae73')
    fig.update_layout(barmode='group');st.plotly_chart(style(fig),use_container_width=True,key='decision_cost')
    a,b=st.columns([1,2])
    size=a.select_slider('Network size',[12,16,20,28,36],value=12,key='decision_size')
    priority=b.selectbox('Compare priority',['Failure recovery','Route-cost control','Simple small network','Control events'],key='decision_priority')
    pair=runs(size,*parameters)
    if priority=='Route-cost control':message='OSPF supports configurable link costs; RIP uses hop count.'
    elif priority=='Simple small network':message='RIP is a candidate for small, simple networks; evaluate its 15-hop limit and recovery behavior.' if size<=8 else 'Evaluate OSPF for this larger design; topology diameter and operational needs also matter.'
    elif priority=='Control events':
        message=f"Model events: RIP {pair['RIP']['summary']['control_messages']}, OSPF {pair['OSPF']['summary']['control_messages']}. Omitted OSPF traffic prevents a real-overhead recommendation."
    else:
        values={p:r['summary']['convergence_ticks'] for p,r in pair.items()}
        message=f"Working path restored: RIP {values['RIP']} steps, OSPF {values['OSPF']} steps under these simulation settings. Validate recovery with timed Cisco trials."
    st.info(message)
    st.caption('Decision support for this experiment, not a production benchmark. Recorded steady-state Cisco probes cannot rank recovery speed.')
