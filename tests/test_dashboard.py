"""Verify scenario filtering and the saved Cisco launcher."""
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'dashboard' / 'app.py'


def test_dashboard_filters_recorded_results():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert len(app.tabs) == 7
    assert len(app.get('plotly_chart')) == 12
    app.radio(key='performance_scenario').set_value('Restored').run(timeout=30)
    assert not app.exception
    assert any('No packet probe' in item.value for item in app.info)
    routes = [item.value for item in app.markdown if 'route-row' in item.value and 'style=' in item.value]
    assert len(routes) == 1
    assert 'OSPF' in routes[0] and 'R1 → R2 → R4' in routes[0]
    app.radio(key='performance_scenario').set_value('Link failure').run(timeout=30)
    assert not app.exception
    routes = [item.value for item in app.markdown if 'route-row' in item.value and 'style=' in item.value]
    assert len(routes) == 2
    assert all('R1 → R3 → R5 → R4' in row for row in routes)


def test_cisco_launch_uses_saved_project():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.button(key='open_RIP').disabled
    with patch('subprocess.Popen') as launch:
        app.button(key='open_RIP').click().run(timeout=30)
        assert not app.exception
        args = launch.call_args.args[0]
        assert Path(args[0]).name == 'PacketTracer.exe'
        assert Path(args[1]).name == 'RIP_Experiment.pkt'
        assert Path(args[1]).exists()



def test_model_state_and_scaling_controls():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.radio(key='failure_protocol').set_value('OSPF')
    app.slider(key='failure_tick').set_value(4).run(timeout=30)
    assert not app.exception
    assert any('Probe delivered' in item.value for item in app.success)
    app.multiselect(key='scale_sizes').set_value([]).run(timeout=30)
    assert not app.exception
    assert any('Choose at least one' in item.value for item in app.info)
    app.selectbox(key='decision_priority').set_value('Control events').run(timeout=30)
    assert not app.exception
    assert any('prevents a real-overhead' in item.value for item in app.info)
