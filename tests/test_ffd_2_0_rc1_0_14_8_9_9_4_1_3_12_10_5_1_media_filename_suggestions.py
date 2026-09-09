from reunion_companion.companion.media_reconciliation import media_filename_suggestion

def test_single_associated_person_gives_high_confidence_canonical_name():
    item={'name':'Glenn S.jpg','contexts':[{'person_id':1,'display_name':'Glenn David Schapel','given_names':'Glenn David','surname':'Schapel','context_type':'Person','event_type':None}]}
    got=media_filename_suggestion(item)
    assert got['suggested_filename']=='Schapel, Glenn David.jpg'
    assert got['confidence']=='High'

def test_same_surname_multiple_people_are_review_not_automatic():
    item={'name':'Thomas Hale Bennett & Orina Florence Grace Burial - 1.jpg','contexts':[
      {'person_id':1,'display_name':'Thomas Hale Bennett Howie','given_names':'Thomas Hale Bennett','surname':'Howie'},
      {'person_id':2,'display_name':'Orina Florence Grace Howie','given_names':'Orina Florence Grace','surname':'Howie'}]}
    got=media_filename_suggestion(item)
    assert got['suggested_filename'].startswith('Howie, Thomas Hale Bennett and Orina Florence Grace')
    assert got['confidence']=='Review'

def test_no_association_does_not_guess():
    got=media_filename_suggestion({'name':'IMG_4832.jpg','contexts':[]})
    assert got['suggested_filename'] is None
    assert got['confidence']=='Review'
