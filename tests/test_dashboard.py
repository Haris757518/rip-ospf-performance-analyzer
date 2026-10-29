"""Verify scenario filtering and the saved Cisco launcher."""
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'dashboard' / 'app.py'


def test_dashboard_uses_only_enterprise_views():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert len(app.tabs)==5
    assert all('Failure Lab' not in tab.label and 'Routing Lab' not in tab.label for tab in app.tabs)
    assert any('No Cisco results recorded for the 12-router' in item.value for item in app.info)
    app.radio(key='performance_scenario').set_value('Restored').run(timeout=30)
    assert not app.exception
    assert not any('route-row' in item.value and '<strong>R1' in item.value for item in app.markdown)


def test_cisco_launch_targets_enterprise_project():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    file=APP.parents[1]/'Enterprise_RIP_Experiment.pkt'
    if not file.exists():
        assert app.button(key='open_RIP').disabled
    else:
        with patch('subprocess.Popen') as launch:
            app.button(key='open_RIP').click().run(timeout=30)
            assert not app.exception
            assert Path(launch.call_args.args[0][1]).name==file.name


def test_shared_enterprise_settings_and_scaling_controls():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    app.slider(key='model_delay').set_value(4).run(timeout=30)
    assert not app.exception
    assert app.multiselect(key='scale_sizes').options==['12','16','20','28','36']
    app.multiselect(key='scale_sizes').set_value([]).run(timeout=30)
    assert not app.exception
    assert any('Choose at least one' in item.value for item in app.info)
    app.selectbox(key='decision_priority').set_value('Control events').run(timeout=30)
    assert not app.exception
    assert any('prevents a real-overhead' in item.value for item in app.info)


def test_enterprise_path_failure_selection():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.selectbox(key='enterprise_path').set_value('R1 → R3 → R5 → R11 → R8 → R12').run(timeout=30)
    assert not app.exception
    assert 'R5–R11' in app.multiselect(key='enterprise_links').options
    assert 'R2–R12' not in app.multiselect(key='enterprise_links').options
    app.multiselect(key='enterprise_links').set_value(['R5–R11','R11–R8']).run(timeout=30)
    app.button(key='enterprise_apply_failure').click().run(timeout=30)
    assert not app.exception
    assert any('Broken together: R5–R11, R11–R8' in x.value for x in app.success)
    app.selectbox(key='enterprise_path').set_value('All links').run(timeout=30)
    assert len(app.multiselect(key='enterprise_links').options)==18
