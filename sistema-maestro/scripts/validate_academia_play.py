#!/usr/bin/env python3
"""Academia Play v4 — JSON Schema, integridad referencial y reglas de dominio.
Validación estructural: no acredita exactitud científica ni eficacia educativa.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from jsonschema import Draft202012Validator
from progress_policy import derive_mastery, validate_invariants, merge_progress as _merge_progress, ProgressConflict

ROOT=Path(__file__).resolve().parents[1]
SC=ROOT/'schemas'

class ContractError(ValueError): pass

def check_schema(obj,filename):
 schema=json.loads((SC/filename).read_text(encoding='utf8'))
 problems=sorted(Draft202012Validator(schema).iter_errors(obj),key=lambda e:list(map(str,e.absolute_path)))
 return [f"schema: {'.'.join(map(str,e.absolute_path)) or 'root'}: {e.message}" for e in problems]

def unique_index(data,kind,key,errors):
 index={}
 for item in data.get(kind,[]):
  ident=item[key]
  if ident in index:errors.append(f'{kind}: duplicate {ident}')
  index[ident]=item
 return index

def validate_manifest(data):
 errors=check_schema(data,'manifest.schema.json')
 if errors:return errors
 ix={k:unique_index(data,k,field,errors) for k,field in [('institutions','institution_id'),('sources','source_id'),('courses','course_id'),('objectives','objective_id'),('oracles','oracle_id'),('engines','engine_id'),('misconceptions','misconception_id'),('activities','activity_id'),('labs','lab_id'),('modules','module_id'),('routes','route_id')]}
 def req(ref,index,where):
  if ref not in ix[index]:errors.append(f'{where}: unknown {index} reference {ref}')
 def check_refs(refs,where):
  for r in refs:
   req(r['source_id'],'sources',where)
   s=ix['sources'].get(r['source_id'])
   if s and not set(r['pages']).issubset(s['inspected_pages']):errors.append(f'{where}: pages not inspected in {r["source_id"]}')
 for course in data['courses']:
  c=course['course_id'];req(course['institution_id'],'institutions',c);req(course['syllabus_source_id'],'sources',c)
  for o in course['objective_ids']:req(o,'objectives',c)
  for r in course['route_ids']:req(r,'routes',c)
  if not course['route_ids']:errors.append(f'{c}: no learning route')
  s=ix['sources'].get(course['syllabus_source_id'])
  if s and s['kind']!='SYLLABUS':errors.append(f'{c}: syllabus source has wrong kind')
 for o in data['objectives']:
  ident=o['objective_id'];req(o['course_id'],'courses',ident);check_refs(o['source_refs'],ident)
  for x in o['prerequisite_ids']:req(x,'objectives',ident)
  for x in o['misconception_ids']:req(x,'misconceptions',ident)
 for m in data['misconceptions']:
  for o in m['objective_ids']:req(o,'objectives',m['misconception_id'])
 for a in data['activities']:
  ident=a['activity_id'];req(a['course_id'],'courses',ident);req(a['oracle_id'],'oracles',ident);check_refs(a['source_refs'],ident)
  for o in a['objective_ids']+a['prerequisite_ids']:req(o,'objectives',ident)
  c=ix['courses'].get(a['course_id'])
  if c and c['course_version']!=a['course_version']:errors.append(f'{ident}: course_version mismatch')
  for f in a['feedback_by_error']:req(f['misconception_id'],'misconceptions',ident)
  families={v['family'] for v in a['variants']}
  if len(families)<2:errors.append(f'{ident}: at least two distinct variant families required')
  v_ids=[v['variant_id'] for v in a['variants']]
  if len(v_ids)!=len(set(v_ids)):errors.append(f'{ident}: duplicate variant_id')
  if a['transfer_variant_id'] not in v_ids:errors.append(f'{ident}: transfer variant missing')
  transfer=next((v for v in a['variants'] if v['variant_id']==a['transfer_variant_id']),None)
  if transfer and transfer['role']!='TRANSFER':errors.append(f'{ident}: transfer variant role invalid')
  if transfer and transfer['item_id'] not in a['mode_item_ids']['learning_path']:errors.append(f'{ident}: route missing its own transfer item')
  if transfer and transfer['item_id'] in a['mode_item_ids']['exam_preparation']:errors.append(f'{ident}: transfer item leaked into exam')
  if not any(v['role']=='EXAM' and v['item_id'] in a['mode_item_ids']['exam_preparation'] for v in a['variants']):errors.append(f'{ident}: exam mode lacks independent exam variant')
  for v in a['variants']:
   if v['role']=='EXAM' and v['item_id'] in a['mode_item_ids']['learning_path']:errors.append(f'{ident}: exam item in learning_path')
  if any('porque es incorrect' in f['explanation'].lower() for f in a['feedback_by_error']):errors.append(f'{ident}: circular feedback')
  all_items={v['item_id'] for v in a['variants']}
  for mode,item_ids in a['mode_item_ids'].items():
   for item in item_ids:
    if item not in all_items:errors.append(f'{ident}: mode {mode} references unknown item {item}')
  if set(a['mode_item_ids']['learning_path'])&set(a['mode_item_ids']['exam_preparation']):errors.append(f'{ident}: exam leakage from learning path')
  if set(a['mode_item_ids']['practice_tutor'])&set(a['mode_item_ids']['exam_preparation']):errors.append(f'{ident}: exam leakage from tutor practice')
 for o in data['oracles']:
  if not o['has_negative'] or not o['has_inconclusive']:errors.append(f"{o['oracle_id']}: negative and INCONCLUSIVE fixtures required")
 for l in data['labs']:
  ident=l['lab_id'];req(l['engine_id'],'engines',ident)
  for o in l['course_objective_refs']:req(o,'objectives',ident)
  for o in l['oracle_ids']:req(o,'oracles',ident)
  if l['reuse_decision']=='CREATE' and (not l['decision_adr'].startswith('ADR-') or not l['considered_alternatives'].strip()):errors.append(f'{ident}: CREATE requires ADR and alternatives')
  if not l['course_objective_refs']:errors.append(f'{ident}: no live objective')
 for mod in data['modules']:
  ident=mod['module_id'];req(mod['course_id'],'courses',ident)
  for o in mod['objective_ids']:req(o,'objectives',ident)
  for d in mod['depends_on']:req(d,'modules',ident)
 for r in data['routes']:
  ident=r['route_id'];req(r['course_id'],'courses',ident);req(r['objective_id'],'objectives',ident)
  if r['unlock_policy']=='DIAGNOSTIC_EQUIVALENCE':
   req(r['diagnostic_oracle_id'],'oracles',ident)
   if not r['diagnostic_evidence_required']:errors.append(f'{ident}: diagnostic evidence required')
  if not r['repeat_access']:errors.append(f'{ident}: repeat_access must be true')
  if not r['mastery_rule']['unassisted_required'] or not r['mastery_rule']['requires_transfer']:errors.append(f'{ident}: weak mastery rule')
 for course in data['courses']:
  for ident in course['objective_ids']:
   if not any(ident in a['objective_ids'] for a in data['activities']):errors.append(f'{ident}: no activity')
   if not any(ident in m['objective_ids'] for m in data['modules']):errors.append(f'{ident}: no module')
   if not any(ident==r['objective_id'] for r in data['routes']):errors.append(f'{ident}: no route')
 def cycles(index,edge,kind):
  visiting=set();visited=set()
  def dfs(node):
   if node in visiting:errors.append(f'{kind}: cycle involving {node}');return
   if node in visited:return
   visiting.add(node)
   for dep in index[node][edge]:
    if dep in index:dfs(dep)
   visiting.remove(node);visited.add(node)
  for n in index:dfs(n)
 cycles(ix['modules'],'depends_on','modules')
 cycles(ix['objectives'],'prerequisite_ids','objectives')
 return errors

def validate_progress(obj, route_rule=None):
 errors=check_schema(obj,'progress.schema.json')
 if errors:return errors
 try:
  validate_invariants(obj, route_rule)
 except ProgressConflict as e:
  errors.append(f'PROGRESS_INVARIANT: {e}')
 return errors

def merge_progress(a,b):
 return _merge_progress(a,b)

ContractError=ProgressConflict

def validate_gate(obj):
 errors=check_schema(obj,'gate.schema.json')
 if errors:return errors
 if obj['result']=='PASS' and (obj['evidence_level']!='E1' or not obj['commands'] or not obj['logs']):errors.append('PASS requires E1 commands and logs')
 if obj['result']=='PASS' and obj['gate_id'] in ('G-SOURCE','G-CURRICULUM','G-DESIGN'):errors.append('design/document gate requires DOC_PASS not PASS')
 if obj['result']=='DOC_PASS' and obj['gate_id'] not in ('G-SOURCE','G-CURRICULUM','G-DESIGN'):errors.append('technical gate cannot use DOC_PASS')
 if obj['result']=='PASS' and obj['gate_id']=='G-DEPLOY' and (not obj['commit_sha'] or obj['deployment_sha']!=obj['commit_sha'] or not obj['workflow_run_id']):errors.append('deployment requires exact SHA and workflow ID')
 return errors

def main():
 p=argparse.ArgumentParser();p.add_argument('file',type=Path);p.add_argument('--kind',choices=['manifest','progress','gate'],default='manifest');args=p.parse_args()
 obj=json.loads(args.file.read_text(encoding='utf8'))
 errors={'manifest':validate_manifest,'progress':validate_progress,'gate':validate_gate}[args.kind](obj)
 for error in errors:print('FAIL:',error)
 if not errors:print(f'PASS {args.kind}: structural and reference checks')
 raise SystemExit(bool(errors))
if __name__=='__main__':main()
