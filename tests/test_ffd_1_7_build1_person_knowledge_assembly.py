from reunion_companion.companion.database import connect
from reunion_companion.companion.person_knowledge import assemble_person_knowledge, knowledge_inventory_text


def seed(db):
    db.executemany(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        [
            (1,"@I1@",1,"James","Knuckey","James Knuckey","M","James /Knuckey/"),
            (2,"@I2@",2,"Elizabeth","Hunter","Elizabeth Hunter","F","Elizabeth /Hunter/"),
            (3,"@I3@",3,"Thomas","Knuckey","Thomas Knuckey","M","Thomas /Knuckey/"),
            (4,"@I4@",4,"Jane","Peters","Jane Peters","F","Jane /Peters/"),
        ],
    )
    db.executemany(
        "INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",
        [
            (10,1,"Birth","1 JUN 1857","Tea Tree Gully, South Australia","Y","Birth memo","BIRT"),
            (11,1,"Occupation","1890","Gilberton, South Australia","Carpenter",None,"OCCU"),
            (12,1,"Religion",None,None,"Church of England",None,"RELI"),
        ],
    )
    db.executemany(
        "INSERT INTO notes(id,person_id,note_type,gedcom_tag,gedcom_note_xref,text,is_referenced) VALUES(?,?,?,?,?,?,?)",
        [
            (20,1,"Note","NOTE",None,"James moved with his family and worked locally.",0),
            (21,1,"Research","_NOTE",None,"Check the exact year of the move.",0),
        ],
    )
    db.executemany("INSERT INTO families(id,gedcom_xref,marriage_date,marriage_place) VALUES(?,?,?,?)",[
        (30,"@F30@","1880","Adelaide, South Australia"),
        (31,"@F31@",None,None),
    ])
    db.executemany("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",[
        (30,1,"Husband"),(30,2,"Wife"),
        (31,3,"Husband"),(31,4,"Wife"),(31,1,"Child"),
    ])
    db.executemany("INSERT INTO sources(id,gedcom_xref,title,text,source_type,display_text) VALUES(?,?,?,?,?,?)",[
        (40,"@S40@","Birth Certificate","SA birth registration","Civil","Birth certificate"),
        (41,"@S41@","Family Bible","Family Bible entry","Private","Family Bible"),
        (42,"@S42@","Marriage Register","Marriage entry","Civil","Marriage register"),
    ])
    db.execute("INSERT INTO event_sources(event_id,source_id,relation) VALUES(10,40,'GEDCOM')")
    db.execute("INSERT INTO note_sources(note_id,source_id,relation) VALUES(20,41,'GEDCOM')")
    db.execute("INSERT INTO family_sources(family_id,source_id,relation) VALUES(30,42,'GEDCOM')")
    db.execute("INSERT INTO citations(id,source_id,owner_scope,person_id,event_id,context_tag,context_path) VALUES(50,40,'event',1,10,'BIRT','INDI/BIRT/SOUR')")
    db.executemany("INSERT INTO media(id,gedcom_xref,file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label) VALUES(?,?,?,?,?,?,?,?)",[
        (60,None,"/tmp/james.jpg","James portrait","image/jpeg",0,"person",None),
        (61,None,"/tmp/birth.pdf","Birth certificate","application/pdf",0,"event","Birth"),
        (62,None,"/tmp/wedding.jpg","Wedding photograph","image/jpeg",0,"family","Marriage"),
    ])
    db.execute("INSERT INTO person_media(person_id,media_id,relation) VALUES(1,60,'GEDCOM')")
    db.execute("INSERT INTO event_media(event_id,media_id,relation) VALUES(10,61,'GEDCOM')")
    db.execute("INSERT INTO family_media(family_id,media_id,relation) VALUES(30,62,'GEDCOM')")
    db.commit()


def test_assembles_structured_person_facts_and_notes(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    k=assemble_person_knowledge(db,1)
    assert k['person']['display_name']=='James Knuckey'
    assert [e['event_type'] for e in k['events']]==['Birth','Occupation','Religion']
    assert [n['note_type'] for n in k['notes']]==['Note','Research']
    assert k['assembly']['narrative_generated'] is False


def test_assembles_relationships_from_both_family_directions(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    rel={(r['relationship'],r['display_name']) for r in assemble_person_knowledge(db,1)['relationships']}
    assert ('Spouse','Elizabeth Hunter') in rel
    assert ('Father','Thomas Knuckey') in rel
    assert ('Mother','Jane Peters') in rel


def test_sources_remain_linked_to_owning_objects(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    k=assemble_person_knowledge(db,1)
    birth=next(e for e in k['events'] if e['event_type']=='Birth')
    note=k['notes'][0]
    marriage=next(f for f in k['families'] if f['id']==30)
    assert birth['sources'][0]['label']=='Birth certificate'
    assert note['sources'][0]['label']=='Family Bible'
    assert marriage['sources'][0]['label']=='Marriage register'
    assert {s['id'] for s in k['sources']}=={40,41,42}
    assert k['citations'][0]['context_path']=='INDI/BIRT/SOUR'


def test_media_includes_person_event_and_family_attachments(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    media=assemble_person_knowledge(db,1)['media']
    assert {(m['owner_scope'],m['title']) for m in media}=={
        ('person','James portrait'),('event','Birth certificate'),('family','Wedding photograph')}


def test_places_are_deduplicated_and_traceable(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    places=assemble_person_knowledge(db,1)['places']
    names={p['name'] for p in places}
    assert names=={'Tea Tree Gully, South Australia','Gilberton, South Australia','Adelaide, South Australia'}
    tea=next(p for p in places if p['name'].startswith('Tea Tree'))
    assert tea['event_ids']==[10]


def test_missing_person_and_inventory_are_safe(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    assert assemble_person_knowledge(db,999) is None
    text=knowledge_inventory_text(db,1)
    assert 'Person Knowledge — James Knuckey' in text
    assert 'Events          3' in text
    assert 'no narrative has been generated' in text
