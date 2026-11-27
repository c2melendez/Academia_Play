"""M1 internal assessment adapter. No public exam feedback or mastery claims."""
import json
import re
from pathlib import Path
from mm110_f01_oracle import Verdict, MAX_LENGTH, MAX_DEGREE
from mm110_f01_oracle_worker import compare_isolated
from mm110_polynomial_worker import verify_isolated

BANK = Path(__file__).resolve().parents[1]/"docs"/"mm110"/"MM110_M1_BANK.json"
ITEMS = tuple(json.loads(BANK.read_text(encoding="utf-8"))["items"])
INDEX = {i["id"]:i for i in ITEMS}

def reduced_form(answer):
    """Recognize sums of distinct nonzero monomials; order is immaterial.
    Exact equivalence is checked separately in the isolated worker.
    """
    if not isinstance(answer,str) or len(answer)>MAX_LENGTH:
        return False
    s=answer.strip().replace("−","-").replace("²","^2").replace("³","^3").replace("×","*")
    if s=="0":
        return True
    term=re.compile(r"\s*([+-]?)\s*(?:(\d+(?:\s*/\s*\d+)?)\s*(?:\*\s*)?)?(x(?:\s*\^\s*(\d+))?)?")
    seen=set()
    pos=0
    while pos<len(s):
        m=term.match(s,pos)
        if not m or m.end()==pos:
            return False
        sign,coef,var,exponent=m.groups()
        if pos and not sign:
            return False
        if not coef and not var:
            return False
        # A trailing multiplication without a variable is not a monomial.
        if not var and "*" in m.group():
            return False
        if coef:
            parts=coef.replace(" ","").split("/")
            if int(parts[0])==0 or (len(parts)==2 and int(parts[1])==0):
                return False
        power=int(exponent) if exponent is not None else (1 if var else 0)
        if power>MAX_DEGREE or (var and power==0) or power in seen:
            return False
        seen.add(power)
        pos=m.end()
    return bool(seen)

def assess_math(item_id,answer):
    """Internal mathematical verdict; not a student session or mastery score."""
    i=INDEX[item_id]
    op=i["operation"]
    args=i["arguments"]
    invalid=Verdict("REJECTED","INVALID_FORMAT_OR_DOMAIN")
    if op=="equivalent":
        v=compare_isolated(args[0],answer)
        if v.status=="VERIFIED" and not reduced_form(answer):
            return Verdict("REJECTED","REQUIRED_REDUCED_FORM")
        return v
    if op=="degree":
        return verify_isolated(op,*args,answer)
    if op=="coefficient":
        if isinstance(answer,str) and "x" in answer:
            return invalid
        return verify_isolated(op,*args,answer)
    if op=="factor_product":
        if not isinstance(answer,(list,tuple)) or len(answer)!=2:
            return invalid
        return verify_isolated(op,*args,answer)
    if op=="division":
        if not isinstance(answer,(list,tuple)) or len(answer)!=2:
            return invalid
        v=verify_isolated(op,*args,*answer)
        if v.status=="VERIFIED" and not all(reduced_form(x) for x in answer):
            return Verdict("REJECTED","REQUIRED_REDUCED_FORM")
        return v
    return invalid

def public_item(item_id):
    i=INDEX[item_id]
    return {**{k:i[k] for k in ("id","family","stage","operation","prompt","reasoning_prompt")},
            "choices":list(i["choices"])}

def assess(item_id, answer, reason_choice, assisted=False):
    """Internal combined assessment. Exam returns only a recording status.
    Persistence, authorization, and exam completion belong to the controller.
    """
    i=INDEX[item_id]
    if type(assisted) is not bool:
        raise ValueError("assisted must be boolean")
    if type(reason_choice) is not int or not 0 <= reason_choice < len(i["choices"]):
        raise ValueError("invalid reasoning choice")
    if i["stage"]=="E" and assisted:
        raise ValueError("assistance forbidden in exam")
    v=assess_math(item_id,answer)
    if v.status=="INCONCLUSIVE":
        return {"status":"RETRY"}
    if v.reason=="INVALID_FORMAT_OR_DOMAIN":
        return {"status":"INVALID_INPUT"}
    correct=reason_choice==i["correct_reason"]
    accepted=v.status=="VERIFIED" and correct
    if i["stage"]=="E":
        # Internal record only: never serialize this as a public response.
        return {"status":"RECORDED","private_assessment":{
            "accepted":accepted,"oracle_status":v.status,
            "reasoning_correct":correct}}
    if v.reason=="REQUIRED_REDUCED_FORM":
        feedback="La expresión es equivalente, pero debes desarrollar y reunir términos semejantes."
    elif v.reason=="REMAINDER_DEGREE":
        feedback="El residuo no nulo debe tener grado menor que el divisor."
    elif v.status!="VERIFIED":
        feedback=i["explanation"]
    elif not correct:
        feedback="El resultado es correcto, pero revisa el fundamento: "+i["explanation"]
    else:
        feedback=i["explanation"]
    return {"status":"ASSESSED","accepted":accepted,"oracle_status":v.status,
            "oracle_reason":v.reason,"reasoning_correct":correct,"assisted":assisted,
            "eligible_evidence":accepted and not assisted and i["stage"] in ("C","T"),
            "feedback":feedback}

def public_assessment(result):
    """Strip private exam results at the public boundary; no mastery awarded."""
    if result["status"]=="RECORDED":
        return {"status":"RECORDED"}
    return dict(result)

