"""Normalize both project CSV formats without inventing measurements."""
import pandas as pd
from core import COLUMNS, validate_records


def read_data(file):
    data=pd.read_csv(file,keep_default_na=False)
    if 'scenario' in data and 'experiment' not in data:
        required={'protocol','scenario','trial','packets_sent','packets_received','capture_method'}
        missing=required-set(data.columns)
        if missing:raise ValueError('Missing V2 columns: '+', '.join(sorted(missing)))
        data=data.rename(columns={'scenario':'experiment','packets_sent':'sent_packets','packets_received':'received_packets','observed_route':'route_path','capture_method':'measurement_basis','notes':'evidence_note'})
        aliases={'normal':'baseline','link failure':'failover','failure':'failover','link_failure':'failover','restored':'recovery','cost demo':'cost_demo'}
        data['experiment']=data.experiment.astype(str).str.strip().str.lower().replace(aliases)
        for col in ('route_path','evidence_note'): 
            if col not in data:data[col]=''
        if (data.measurement_basis.astype(str).str.strip()=='').any():raise ValueError('V2 rows require capture_method provenance')
        if 'convergence_ms' in data:
            data['convergence_s']=pd.to_numeric(data.convergence_ms.mask(data.convergence_ms.eq('')),errors='raise')/1000
        else:data['convergence_s']=''
        # Derive only an explicit router-to-router route, never from a synthetic model.
        import re
        def hops(path):
            parts=re.split(r'\s*(?:->|→)\s*',str(path).strip())
            return len(parts)-1 if parts and all(re.fullmatch(r'R[1-9]\d*',p) for p in parts) else ''
        data['route_hops']=data.route_path.map(hops)
    missing=set(COLUMNS)-set(data.columns)
    if missing:raise ValueError('Missing columns: '+', '.join(sorted(missing)))
    data['protocol']=data.protocol.astype(str).str.strip().str.upper()
    errors=validate_records(data.to_dict('records'))
    if errors:raise ValueError('; '.join(f'Row {r}: {m}' for r,m in errors[:5]))
    for col in ('trial','convergence_s','sent_packets','received_packets','route_hops'):
        data[col]=pd.to_numeric(data[col],errors='coerce').astype(float)
    if 'router_count' not in data:data['router_count']=5
    data['router_count']=pd.to_numeric(data.router_count,errors='raise')
    if ((data.router_count<2)|(~data.router_count.map(lambda x:float(x).is_integer()))).any():raise ValueError('router_count must be an integer of at least 2')
    keys=['protocol','experiment','trial','measurement_basis','router_count']
    if data.duplicated(keys).any():raise ValueError('Duplicate trial rows for the same protocol, scenario, method and network size')
    return data
