from reunion_companion.companion.beta3_quality import era_bucket, filter_quality_items, quality_drilldown

def test_rolling_era_boundaries():
    assert era_bucket(1926,2026)[0]=='100-200'
    assert era_bucket(1927,2026)[0]=='last-100'
    assert era_bucket(1826,2026)[0]=='over-200'
    assert era_bucket(1827,2026)[0]=='100-200'
    assert era_bucket(None,2026)[0]=='unknown'

def test_event_then_era_filtering():
    items=[{'event_type':'Birth','year':1950},{'event_type':'Birth','year':1850},{'event_type':'Death','year':2000},{'event_type':'Birth','year':None}]
    assert quality_drilldown(items,2026)['by_type']=={'Birth':3,'Death':1}
    births=filter_quality_items(items,'Birth',current_year=2026)
    assert len(births)==3
    assert filter_quality_items(births,era='last-100',current_year=2026)==[{'event_type':'Birth','year':1950}]
