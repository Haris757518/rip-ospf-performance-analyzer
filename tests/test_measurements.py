import io
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dashboard'))
from measurements import read_data

HEADER='protocol,scenario,trial,router_count,packets_sent,packets_received,convergence_ms,observed_route,capture_method,notes\n'


def test_v2_preserves_method_and_converts_units():
    data=read_data(io.StringIO(HEADER+'ospf,failure,1,5,10,8,250,R1 -> R3 -> R5 -> R4,event clock,trial capture\n'))
    row=data.iloc[0]
    assert row.protocol=='OSPF' and row.experiment=='failover'
    assert row.convergence_s==.25 and row.route_hops==3
    assert row.measurement_basis=='event clock'


@pytest.mark.parametrize('row',[
    'RIP,baseline,1,5,4,5,,R1 -> R2 -> R4,console,',
    'RIP,baseline,1,5,4,4,bad,R1 -> R2 -> R4,console,',
    'RIP,baseline,1,5,4,4,-1,R1 -> R2 -> R4,console,',
    'RIP,baseline,1,5,4,4,,R1 -> R2 -> R4,,',
    'RIP,baseline,1,5.5,4,4,,R1 -> R2 -> R4,console,',
])
def test_invalid_v2_rows_rejected(row):
    with pytest.raises(ValueError):read_data(io.StringIO(HEADER+row+'\n'))


def test_blank_measurements_are_not_zero():
    data=read_data(io.StringIO(HEADER+'OSPF,recovery,1,5,,,,R1 -> R2 -> R4,route table,\n'))
    assert data.sent_packets.isna().all() and data.convergence_s.isna().all()
    assert data.iloc[0].route_hops==2


def test_duplicate_trials_rejected():
    row='RIP,baseline,1,5,4,4,,R1 -> R2 -> R4,console,\n'
    with pytest.raises(ValueError,match='Duplicate'):read_data(io.StringIO(HEADER+row+row))


def test_existing_recorded_evidence_still_loads():
    data=read_data(Path(__file__).resolve().parents[1]/'data/measured_results.csv')
    assert len(data)==5 and data.convergence_s.isna().all()
