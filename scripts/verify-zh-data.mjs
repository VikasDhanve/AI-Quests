import assert from 'node:assert/strict';import fs from 'node:fs';
const root='public/ai-quests/content/api/snapshot/20261023-141713/';const protectedKeys=new Set(['collection_id','document_id','id','url','uri','src','file_name','type','record_id','validity','patient_number','eye_color','diagnosis_severity','diagnosis_type','risk','mode','theme','color','iconId','icon_id','token_id']);let leaves=0,tracks=0,controls=0;
const variables=s=>[...s.matchAll(/\{\{(.*?)\}\}/g)].map(x=>x[1].trim()).filter(x=>['count','total','number','google_logo','partner_logo'].includes(x)).sort();
const cues=s=>s.split('\n').filter(x=>/^(?:\d\d:)?\d\d:\d\d\.\d+\s+-->/.test(x.trim()));
function check(a,b,p=''){
 assert.equal(typeof b,typeof a,p);if(a===null){assert.equal(b,null,p);return}if(typeof a==='object'){assert.deepEqual(Object.keys(b),Object.keys(a),p);for(const k of Object.keys(a))check(a[k],b[k],p+'/'+k);return}leaves++;
 if(typeof a!=='string'){assert.equal(b,a,p);controls++;return}const k=p.split('/').at(-1);
 if(protectedKeys.has(k)||p.includes('/key_concept_tags/')||(/^(?:https?:|\/ai-quests\/|assets\/)/.test(a))||(['habitat','uv_rating','region','gender'].includes(k)&&/^[a-z_-]+$/.test(a))){assert.equal(b,a,p);controls++}
 assert.deepEqual(variables(b),variables(a),p);if(a.startsWith('WEBVTT')){assert.deepEqual(cues(b),cues(a),p);assert.match(b,/[\u4e00-\u9fff]/,p);tracks++}
}
for(const name of ['sitewide','planet_page','home_page','not_found_page','flood_prediction','blindness_prevention','mapping_brain'])check(JSON.parse(fs.readFileSync(root+'en_us/'+name+'.json')),JSON.parse(fs.readFileSync(root+'zh_cn/'+name+'.json')),name);
assert.equal(tracks,12);const report={passed:true,checked_leaves:leaves,unchanged_control_values:controls,subtitle_tracks:tracks};fs.writeFileSync('reports/zh-data-validation.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
