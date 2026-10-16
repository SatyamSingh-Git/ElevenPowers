"""Authored Node case assets with integer accounting and replay contracts."""

BASE = '''class Orders {
  constructor(stock,prices={}) { this.stock={...stock};this.prices={...prices};this.rows={}; }
  reserve(id,sku,qty,now=0,ttl=10) {
    if(this.rows[id]) {const r=this.rows[id];return r.sku===sku&&r.qty===qty;}
    if(!Number.isSafeInteger(qty)||qty<=0) throw new RangeError('qty');
    if((this.stock[sku]||0)<qty) return false;
    this.stock[sku]-=qty;this.rows[id]={sku,qty};return true;
  }
  available(sku,now) {return this.stock[sku]||0;}
}
module.exports={Orders};
'''

REFERENCE = '''class Orders {
  constructor(stock,prices={}) {
    this.stock={...stock};this.prices={...prices};this.rows={};this.seen={};
    for(const n of Object.values(stock)) if(!Number.isSafeInteger(n)||n<0) throw new RangeError('stock');
    for(const p of Object.values(prices)) if(!/^[0-9]+$/.test(p)) throw new RangeError('price');
  }
  _qty(n) {if(!Number.isSafeInteger(n)||n<=0) throw new RangeError('qty');}
  _time(now) {if(!Number.isSafeInteger(now)||now<0) throw new RangeError('time');}
  expire(now) {
    this._time(now);
    for(const r of Object.values(this.rows)) if(!r.expired&&now>=r.until) {
      this.stock[r.sku]+=r.qty-r.fulfilled;r.expired=true;
    }
  }
  reserve(id,sku,qty,now=0,ttl=10) {
    this._qty(qty);this._time(now);this._qty(ttl);
    if(typeof id!=='string'||typeof sku!=='string') throw new RangeError('identity');
    this.expire(now);
    if(Object.hasOwn(this.rows,id)) {const r=this.rows[id];return !r.expired&&r.sku===sku&&r.qty===qty;}
    if((this.stock[sku]||0)<qty) return false;
    this.stock[sku]-=qty;
    this.rows[id]={sku,qty,until:now+ttl,expired:false,fulfilled:0,refunded:0};return true;
  }
  available(sku,now) {if(now!==undefined) this.expire(now);return this.stock[sku]||0;}
  fulfill(id,qty,now=0) {
    this._qty(qty);this._time(now);this.expire(now);const r=this.rows[id];
    if(!r||r.expired||r.fulfilled+qty>r.qty) return null;
    r.fulfilled+=qty;return BigInt(this.prices[r.sku]||'0')*BigInt(qty);
  }
  refund(id,qty) {
    this._qty(qty);const r=this.rows[id];
    if(!r||r.refunded+qty>r.fulfilled) return null;
    r.refunded+=qty;this.stock[r.sku]+=qty;
    return BigInt(this.prices[r.sku]||'0')*BigInt(qty);
  }
  dumps() {return JSON.stringify({version:2,stock:this.stock,prices:this.prices,rows:this.rows,seen:this.seen});}
  static loads(text) {
    try {
      const v=JSON.parse(text);
      if(!v||v.version!==2||!v.stock||!v.prices||!v.rows||!v.seen) throw new RangeError('snapshot');
      const result=new Orders(v.stock,v.prices);result.rows=v.rows;result.seen=v.seen;
      for(const r of Object.values(v.rows)) if(typeof r.sku!=='string'||!Number.isSafeInteger(r.qty)||r.qty<1||!Number.isSafeInteger(r.until)) throw new RangeError('row');
      return result;
    } catch(error) {throw new RangeError('snapshot');}
  }
  replay(events) {
    if(!Array.isArray(events)) throw new RangeError('events');
    const clone=Orders.loads(this.dumps());
    for(const e of events) {
      if(!e||typeof e.event!=='string'||!['reserve','fulfill','refund','expire'].includes(e.op)||!Array.isArray(e.args)) throw new RangeError('event');
      const signature=JSON.stringify([e.op,e.args]);
      if(Object.hasOwn(clone.seen,e.event)) {
        if(clone.seen[e.event]!==signature) throw new RangeError('conflict');
        continue;
      }
      const result=clone[e.op](...e.args);
      if(result===false||result===null) throw new RangeError('rejected');
      clone.seen[e.event]=signature;
    }
    Object.assign(this,clone);
  }
}
module.exports={Orders};
'''

REQUESTS = [
    'Extend Orders(stock,prices={}) reservations: reserve(id,sku,qty,now=0,ttl=10) expires earlier holds before allocation, positive safe-integer qty/ttl and nonnegative safe-integer now validated before any mutation. expire(now) releases unfulfilled stock exactly at deadline; available(sku,now) optionally expires first. Identical live retries succeed without extending deadline; conflicting or expired-ID reuse fails unchanged. No overselling or double release; SKU isolation and existing signatures remain.',
    'Add fulfill(id,qty,now=0) and refund(id,qty), returning exact BigInt cents or null for unknown/ineligible/over-quantity operations. Prices are nonnegative decimal integer strings (missing price means0). fulfill expires first and can partially fulfill a live hold; refund is limited to fulfilled-but-unrefunded quantity and returns that stock once. Expiry releases only unfulfilled units, including after partial refunds. Reject nonpositive/non-safe quantities with RangeError before mutation. Preserve exact arithmetic beyond Number.MAX_SAFE_INTEGER.',
    'Add dumps()->version2 JSON string and static Orders.loads(text)->independent Orders. Preserve stock, decimal-string prices, hold identities/deadlines, fulfillment/refund totals and replay IDs if present. Expiry after restoration must release once; identical retries must not extend original deadlines. Reject malformed/nonobject/unsupported-version/missing-fields snapshots with RangeError. Retain all earlier accounting and validation contracts.',
    'Add replay(events), atomically applying {event:string,op:reserve|fulfill|refund|expire,args:array}. Exact duplicate event IDs are skipped, including across snapshot/restart. A conflicting repeat, unknown operation, invalid arguments or rejected operation throws RangeError and leaves the entire original state unchanged. Successful expiry events can have no return value. Preserve all previous contracts and exact BigInt accounting.'
]

PUBLIC = '''const test=require('node:test'),assert=require('node:assert/strict');
const {Orders}=require('../service.cjs');
test('core reservation',()=>{
 const o=new Orders({x:4,y:2});assert.equal(o.reserve('a','x',3),true);
 assert.equal(o.reserve('a','x',3),true);assert.equal(o.reserve('a','x',2),false);
 assert.equal(o.available('x'),1);assert.equal(o.reserve('b','x',2),false);assert.equal(o.available('y'),2);
});
'''
