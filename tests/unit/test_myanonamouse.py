from __future__ import annotations

from ptsites.trackers.myanonamouse import MainClass


def test_details_support_named_snatch_summary_counts() -> None:
    tracker = MainClass()
    content = '''
        "leeching":{"name":"Leeching Torrents","count":2,"size":null},
        "seedUnsat":{"name":"Seeding - Not Yet Satisfied","count":7,"size":null}
    '''
    details = tracker.details_selector['details']

    assert tracker.get_detail_value(content, details['seeding']) == '7'
    assert tracker.get_detail_value(content, details['leeching']) == '2'
