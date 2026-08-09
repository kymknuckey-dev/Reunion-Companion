from reunion_companion.discovery.differential_verification import ByteSpanDelta,DifferentialResult
from reunion_companion.discovery.noise_suppression import CorpusProbeResult,ProbeSpec,SpanAssessment,SuppressedDifferential
from reunion_companion.discovery.canonical_regions import extract_canonical_spans,build_regions,region_overlaps

def A(i,start,cat="UNKNOWN",text="x"):
    b=ByteSpanDelta("replace",start,start+8,start,start+8,"00","01",text,text)
    return SpanAssessment(i,cat,.35,False,"t",b)
def R(pid,label,ass):
    raw=DifferentialResult(label,"b","a","bh","ah",100,100,tuple(x.span for x in ass),8*len(ass),8*len(ass),(),(),())
    sd=SuppressedDifferential(raw,tuple(ass),tuple(x for x in ass if x.category=="TEXT_SEMANTIC_CANDIDATE"),(),tuple(x for x in ass if x.category=="UNKNOWN"))
    return CorpusProbeResult(ProbeSpec(pid,label,"MODIFY","b","a"),sd)

def test_recurrence():
    repeated="same opaque"
    rs=[R("p1","Birth Date",[A(1,100,text=repeated),A(2,140,text="unique")])]
    rs += [R(f"p{i}",f"Field{i}",[A(1,100,text=repeated)]) for i in range(2,9)]
    rs += [R("p9","Field9",[A(1,100,text="another")])]
    spans,_=extract_canonical_spans(rs)
    cats={(s.probe_id,s.assessment_index):s.region_category for s in spans}
    assert cats[("p1",1)]=="RECURRENT_SAVE_NOISE"
    assert cats[("p1",2)]=="PROBE_SPECIFIC_SEMANTIC"

def test_merge():
    rs=[R("p1","Birth Date",[A(1,100,"TEXT_SEMANTIC_CANDIDATE","[[pt:1]]"),A(2,120,"TEXT_SEMANTIC_CANDIDATE","Test Probe")])]
    spans,_=extract_canonical_spans(rs)
    regs=build_regions(rs,spans)
    assert len(regs)==1 and regs[0].span_count==2

def test_overlap():
    rs=[R("p1","Memo",[A(1,100,"TEXT_SEMANTIC_CANDIDATE","[[pt:1]]")]),R("p2","Marriage",[A(1,200,"TEXT_SEMANTIC_CANDIDATE","[[pt:2]]")])]
    spans,_=extract_canonical_spans(rs)
    ov=region_overlaps(build_regions(rs,spans))
    assert ov and ov[0].shared_signatures>=1
