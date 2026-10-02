"""Literal, hand-derived behavior expectations outside candidate imports."""
import base64


def queue():
    rows=[]
    def add(name,steps,results,pending=0,done=None):
        rows.append((name,{'steps':steps}, {'results':results,'pending':pending,'done':done or {}}))
    e=['enqueue','t','a',{'x':1}];c=['claim','t','w',0,10]
    add('ordinary_lifecycle',[e,c,['ack','t','a',1,1,'ok']], [True,['a',{'x':1},1],True],done={'a':'ok'})
    add('empty_claim',[['claim','t','w',0,10]],[None])
    add('retry_same_payload',[e,['enqueue','t','a',{'x':1}]], [True,False],1)
    add('conflicting_retry_rollback',[e,['enqueue','t','a',{'x':2}],c],[True,{'exception':'ValueError'},['a',{'x':1},1]],1)
    add('tenant_payload_isolation',[e,['enqueue','other','a',2],c],[True,True,['a',{'x':1},1]],1)
    add('active_lease_excluded',[e,c,['claim','t','z',9,5]],[True,['a',{'x':1},1],None],1)
    add('expiry_exact',[e,c,['claim','t','z',10,5]],[True,['a',{'x':1},1],['a',{'x':1},2]],1)
    add('stale_ack_rejected',[e,c,['claim','t','z',10,5],['ack','t','a',1,11,'bad']],[True,['a',{'x':1},1],['a',{'x':1},2],False],1)
    add('expired_ack_rejected',[e,c,['ack','t','a',1,10,'bad']],[True,['a',{'x':1},1],False],1)
    add('unknown_ack_rejected',[['ack','t','missing',1,0,'bad']],[False])
    add('completed_ack_rejected',[e,c,['ack','t','a',1,1,'ok'],['ack','t','a',1,2,'bad']],[True,['a',{'x':1},1],True,False],done={'a':'ok'})
    add('renew_never_shortens',[e,c,['renew','t','a',1,1,2],['claim','t','z',4,5]],[True,['a',{'x':1},1],True,None],1)
    add('renew_extends',[e,c,['renew','t','a',1,8,10],['claim','t','z',10,5],['ack','t','a',1,17,'ok']],[True,['a',{'x':1},1],True,None,True],done={'a':'ok'})
    add('stale_renew_rejected',[e,c,['claim','t','z',10,5],['renew','t','a',1,11,100],['claim','t','z',15,5]],[True,['a',{'x':1},1],['a',{'x':1},2],False,['a',{'x':1},3]],1)
    add('completed_retry',[e,c,['ack','t','a',1,1,'ok'],e],[True,['a',{'x':1},1],True,False],done={'a':'ok'})
    add('durable_reopen',[e,c,['reopen'],['ack','t','a',1,1,{'nested':[1,2]}],['reopen']],[True,['a',{'x':1},1],None,True,None],done={'a':{'nested':[1,2]}})
    add('fifo_and_live_skip',[e,['enqueue','t','b',2],c,['claim','t','z',1,5]],[True,True,['a',{'x':1},1],['b',2,1]],2)
    add('canonical_payload',[['enqueue','t','a',{'a':1,'b':2}],['enqueue','t','a',{'b':2,'a':1}]],[True,False],1)
    add('invalid_lease_is_atomic',[e,['claim','t','w',0,True],c],[True,{'exception':'ValueError'},['a',{'x':1},1]],1)
    add('invalid_token_is_atomic',[e,c,['ack','t','a',True,1,'bad']],[True,['a',{'x':1},1],{'exception':'ValueError'}],1)
    add('invalid_time_is_atomic',[e,['claim','t','w',-1,10],c],[True,{'exception':'ValueError'},['a',{'x':1},1]],1)
    add('tenant_ack_isolation',[e,c,['ack','other','a',1,1,'bad']],[True,['a',{'x':1},1],False],1)
    rows.append(('competing_workers',{'concurrent':True},{'claimed':32,'unique':32,'tokens':[1],'pending':32}))
    return rows


def planner():
    rows=[]
    def graph(**nodes):
        return {n:{'deps':deps,'stamp':'1'} for n,deps in nodes.items()}
    def add(name,old,new,changed,rebuild=None,removed=None,error=False):
        rows.append((name,{'old':old,'new':new,'changed':changed},
                     {'exception':'ValueError'} if error else {'result':{'rebuild':rebuild or [],'removed':removed or []},'unchanged_inputs':True,'summary':{'count':len(rebuild or []),'removed':len(removed or [])}}))
    chain=graph(a=[],b=['a'],c=['b'],x=[])
    add('empty',{}, {}, [],[])
    add('unchanged',chain,chain,[],[])
    add('transitive',chain,chain,['a'],['a','b','c'])
    add('only_consumer',chain,chain,['b'],['b','c'])
    add('disconnected',chain,chain,['x'],['x'])
    add('stamp_discovery',chain,{**chain,'a':{'deps':[],'stamp':'2'}},[],['a','b','c'])
    add('new_node',chain,{**chain,'d':{'deps':['c'],'stamp':'1'}},[],['d'])
    add('deleted_old_chain',chain,graph(b=[],c=['b'],x=[]),[],['b','c'],['a'])
    add('old_edge_propagation',chain,graph(a=[],b=[],c=['b'],x=[]),['a'],['a','b','c'])
    add('dep_change_discovery',chain,graph(a=[],b=['x'],c=['b'],x=[]),[],['b','c'])
    add('rename',chain,graph(z=[],b=['z'],c=['b'],x=[]),[],['z','b','c'],['a'])
    add('delete_all',chain,{},[],[],['a','b','c','x'])
    diamond=graph(a=[],b=['a'],c=['a'],d=['b','c'],z=[])
    add('diamond',diamond,diamond,['a'],['a','b','c','d'])
    roots=graph(a=[],b=[],c=['b'],d=['a'])
    add('ready_lexical',roots,roots,['a','b'],['a','b','c','d'])
    add('duplicate_changed',chain,chain,['b','a','b'],['a','b','c'])
    add('duplicate_deps',chain,{**chain,'b':{'deps':['a','a'],'stamp':'1'}},[],[])
    add('reordered_deps',diamond,{**diamond,'d':{'deps':['c','b'],'stamp':'1'}},[],[])
    add('current_cycle',{},graph(a=['b'],b=['a']),[],error=True)
    add('old_cycle',graph(a=['a']),{},[],error=True)
    add('unaffected_cycle',graph(a=[],x=['y'],y=['x']),graph(a=[],x=['y'],y=['x']),['a'],error=True)
    add('dangling_dep',{},graph(a=['missing']),[],error=True)
    add('malformed_graph',{}, {'a':{'deps':'bad','stamp':'1'}},[],error=True)
    add('unknown_change',chain,chain,['missing'],error=True)
    deep=graph(**{f'n{i:02}':[] if i==0 else [f'n{i-1:02}'] for i in range(40)})
    add('deep_chain',deep,deep,['n00'],list(deep))
    return rows


def cache():
    # The worker exposes observations; these expected traces are controller-owned.
    expectations={
        'basic':[1,1,1], 'none':[None,None,1], 'coalesce':[[1,1],1],
        'tenant_isolation':[1,2,1,2], 'expiry':[1,1,2,2],
        'completion_ttl':[1,1,2,2], 'cancel_waiter':['CancelledError',1,1],
        'failure_retry':['LookupError',2,2], 'invalidate_cached':[1,2,2],
        'invalidate_flight':[1,2,2,2], 'reverse_completions':[2,1,2,2],
        'double_invalidation':[1,2,3,3,3], 'old_cleanup_new_flight':[1,2,2,2],
        'lru_hit':[1,2,1,3,1,4,4], 'tenant_invalidation':[1,2,2,3,3],
        'close_pending':['CancelledError','RuntimeError','RuntimeError',1],
        'close_idempotent':['RuntimeError'], 'invalid_ttl':['ValueError']*5,
        'invalid_capacity':['ValueError']*4, 'invalid_key':['ValueError']*4,
        'all_waiters_cancel':['CancelledError','CancelledError',1,1],
        'failed_old_new_generation':['LookupError',2,2,2],
    }
    return [(name,{'scenario':name},value) for name,value in expectations.items()]


def stream():
    rows=[]
    def add(name,chunks,expected,final=False):
        rows.append((name,{'chunks':[base64.b64encode(c).decode() for c in chunks], 'final':final},expected))
    a=b'{"id":"a","value":1}\n'; b=b'{"id":"b","value":2}\n'
    def expected(outputs,offset,pending=b'',seen=None,finished=False,errors=None):
        return {'outputs':outputs,'errors':errors or ['']*len(outputs),'offset':offset,
                'pending':base64.b64encode(pending).decode(),'seen':seen or {},'finished':finished,'rollback':True,'detached':True,'restored':True}
    si={'a':'["int",1]'}
    add('one_line',[a],expected([[{'id':'a','value':1}]],len(a),seen=si))
    add('empty',[b''],expected([[]],0))
    add('final_tail',[a[:-1]],expected([[{'id':'a','value':1}]],len(a)-1,seen=si,finished=True),True)
    add('split_record',[a[:8],a[8:]],expected([[],[{'id':'a','value':1}]],len(a),seen=si))
    raw='{"id":"a","value":"€😀"}\r\n'.encode()
    split=raw.index('€'.encode())+1
    add('split_utf8',[raw[:split],raw[split:]],expected([[],[{'id':'a','value':'€😀'}]],len(raw),seen={'a':'["str","€😀"]'}))
    add('split_crlf',[a[:-1]+b'\r',b'\n'],expected([[],[{'id':'a','value':1}]],len(a)+1,seen=si))
    add('duplicate_id',[a,a],expected([[{'id':'a','value':1}],[]],2*len(a),seen=si))
    conflict=b'{"id":"a","value":3}\n'
    add('conflict_chunk_rollback',[a,b+conflict],expected([[{'id':'a','value':1}],[]],len(a),seen=si,errors=['','ValueError']))
    add('malformed_chunk_rollback',[b+b'{bad}\n'],expected([[]],0,errors=['ValueError']))
    add('retry_after_rejection',[b'{bad}\n',a],expected([[],[{'id':'a','value':1}]],len(a),seen=si,errors=['ValueError','']))
    add('blank_lines',[b' \r\n\n'+a],expected([[{'id':'a','value':1}]],len(a)+4,seen=si))
    add('invalid_utf8',[b'\xff'],expected([[]],0,errors=['ValueError']))
    add('incomplete_utf8_final',[b'\xe2'],expected([[]],0,errors=['ValueError']),True)
    add('invalid_json_final',[b'{"id":'],expected([[]],0,errors=['ValueError']),True)
    add('bool_not_int',[a,b'{"id":"a","value":true}\n'],expected([[{'id':'a','value':1}],[]],len(a),seen=si,errors=['','ValueError']))
    add('float_not_int',[a,b'{"id":"a","value":1.0}\n'],expected([[{'id':'a','value':1}],[]],len(a),seen=si,errors=['','ValueError']))
    for name,raw in [('nan',b'{"id":"a","value":NaN}\n'),('duplicate_member',b'{"id":"a","id":"b","value":1}\n'),('extra_member',b'{"id":"a","value":1,"x":0}\n'),('empty_id',b'{"id":"","value":1}\n')]:
        add(name,[raw],expected([[]],0,errors=['ValueError']))
    raw=b'{"id":"a","value":{"b":2,"a":[null,true]}}\n';again=b'{"value":{"a":[null,true],"b":2},"id":"a"}\n'
    add('canonical_nested',[raw,again],expected([[{'id':'a','value':{'b':2,'a':[None,True]}}],[]],len(raw)+len(again),seen={'a':'["dict",[["a",["list",[["none"],["bool",true]]]],["b",["int",2]]]]'}))
    add('partial_checkpoint',[b'\xe2',b'\x82\xac'],expected([[],[]],3,pending='€'.encode()))
    rows += [('closed_feed',{'special':'closed'},['ValueError']),
             ('invalid_checkpoints',{'special':'invalid_checkpoints'},['ValueError']*7),
             ('sink_retry',{'special':'sink_retry'},{'first_error':'LookupError','unchanged':True,'outputs':[[{'id':'a','value':1}],[{'id':'a','value':1}]],'offset':len(a)})]
    return rows


SCENARIOS={'lease-queue':queue,'async-cache':cache,'build-planner':planner,'resumable-stream':stream}
