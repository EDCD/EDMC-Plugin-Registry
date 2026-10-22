"""Tests for the offline checks in validate_plugin."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import validate_plugin as vp  # noqa: E402

SHA:str = 'a' * 64
BASE:dict = {
    'pluginName': 'Demo', 'pluginVer': '1.2.3', 'autoUpdateEnabled': False, 'autoInstallEnabled': False,
    'pluginAuthors': ['Some Author'], 'pluginMainLink': 'https://github.com/Owner/Demo', 'pluginLastUpdate': '2026-01-01',
    'pluginDirName': 'Demo', 'pluginCategory': ['Utility'], 'pluginDesc': 'Demo plugin.', 'pluginLastTestedEDMC': '6.1.2',
    'pluginLicense': 'MIT', 'pluginZip': 'https://github.com/Owner/Demo/releases/download/1.2.3/Demo.zip',
    'pluginHash': SHA, 'pluginVT': f'https://www.virustotal.com/gui/file/{SHA}',
}


def bump(**kw) -> dict:
    """BASE with a version bump and overrides."""
    return {**BASE, 'pluginVer': '1.3.0', **kw}


def verified() -> vp.Report:
    """Report for an entry whose network checks passed."""
    rep = vp.Report()
    rep.vt_ok = True
    return rep


def test_valid_entry_is_clean():
    rep = vp.Report()
    vp.check_schema(BASE, rep)
    vp.check_vt_link(BASE, rep)
    assert rep.errors == [] and rep.warnings == []


def test_schema_errors():
    rep = vp.Report()
    bad:dict = {**BASE, 'pluginVer': '1.2', 'pluginLastUpdate': '13/12/2025', 'pluginCategory': [], 'pluginHash': 'abc'}
    del bad['pluginDesc']
    vp.check_schema(bad, rep)
    assert len(rep.errors) == 5


def test_lenient_fields_only_warn():
    rep = vp.Report()
    vp.check_schema({**BASE, 'pluginCategory': ['Mining', 'Colonisation'], 'pluginLicense': 'MIT License', 'pluginVer': 'v1.2.3'}, rep)
    assert rep.errors == [] and len(rep.warnings) == 3 and rep.blockers == []


def test_foreign_zip_blocks():
    rep = vp.Report()
    vp.check_schema({**BASE, 'pluginZip': 'https://github.com/Other/Demo/releases/download/1/Demo.zip'}, rep)
    assert rep.blockers and rep.errors == []


def test_vt_link_hash_mismatch():
    rep = vp.Report()
    vp.check_vt_link({**BASE, 'pluginVT': f'https://www.virustotal.com/gui/file/{"b" * 64}'}, rep)
    assert rep.errors

    rep = vp.Report()
    vp.check_vt_link({**BASE, 'pluginVT': 'https://www.virustotal.com/gui/url/abc'}, rep)
    assert rep.errors == [] and SHA in rep.warnings[0]


def test_pick_file():
    assert vp.pick_file([('M', 'plugins/Demo.json')], vp.Report()) == 'plugins/Demo.json'
    assert vp.pick_file([('M', 'master_plugin_list.json')], vp.Report()) is None
    assert vp.pick_file([('D', 'plugins/Demo.json')], vp.Report()) is None
    assert vp.pick_file([('M', 'plugins/A.json'), ('M', 'plugins/B.json')], vp.Report()) is None


def test_eligible_update():
    assert vp.ineligible(bump(), BASE, 'owner', verified()) == []
    assert vp.ineligible(bump(), BASE, 'some author', verified()) == []


def test_ineligible_cases():
    assert vp.ineligible(bump(), None, 'owner', verified())
    assert vp.ineligible(bump(), BASE, 'stranger', verified())
    assert vp.ineligible(bump(), BASE, 'owner', vp.Report())
    assert vp.ineligible(BASE, BASE, 'owner', verified())
    assert vp.ineligible(bump(pluginVer='1.2.2'), BASE, 'owner', verified())
    assert vp.ineligible(bump(pluginMainLink='https://github.com/Evil/Demo'), BASE, 'evil', verified())
    assert vp.ineligible(bump(pluginAuthors=['owner', 'evil']), BASE, 'owner', verified())


def test_repo_of():
    assert vp.repo_of('https://github.com/Owner/Demo.git') == ('github.com', 'owner', 'owner/demo')
    assert vp.repo_of('https://gitlab.com/inutt/edmc-x/-/releases/v1/downloads/x.zip') == ('gitlab.com', 'inutt', 'inutt/edmc-x')
    assert vp.repo_of('https://edrecon.com') is None
