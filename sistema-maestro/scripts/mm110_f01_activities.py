"""Original F01 activities; separate content, exact oracle, and reasoning checks.
No learner identity or persistence. Expected expressions must remain server-side.
"""
from dataclasses import dataclass
from mm110_f01_oracle import compare, Verdict

@dataclass(frozen=True)
class Item:
    item_id: str
    mode: str
    family: str
    prompt: str
    expected: str
    reasoning_prompt: str
    choices: tuple
    correct_reason: int
    hints: tuple
    explanation: str
    errors: tuple = ()
    required_form: str = "equivalent"

ITEMS = (
    Item("f01-route-expand","learning_path","expansion",
         "Desarrolla 7(2x-3). Escribe el polinomio sin paréntesis.","14x-21",
         "¿Qué operación justifica tu resultado?",
         ("Multiplicar únicamente 2x por 7","Multiplicar ambos términos por 7","Sumar 7 a cada término"),1,
         ("Identifica el factor exterior.","Aplica a(b+c)=ab+ac."),
         "El factor 7 multiplica 2x y -3: los productos son 14x y -21.",
         (("14x-3","f01-omit"),("14x+21","f01-sign")),"expanded"),
    Item("f01-route-repair","learning_path","repair",
         "Corrige la expresión 5x-4 para que sea equivalente a 5(x-4).","5x-20",
         "¿Cuál era el error?",
         ("Se omitió multiplicar el término -4 por 5","Se debía sumar 5 a x","La expresión era válida para todo x"),0,
         ("Compara los términos constantes.","Distribuye 5 también sobre -4."),
         "El término constante correcto es -20, porque 5 multiplica ambos sumandos.",
         (("5x-4","f01-omit"),("5x+20","f01-sign")),"expanded"),
    Item("f01-route-transfer","learning_path","contextual",
         "Se cobra 8 lempiras por unidad de un pedido de x unidades y por 6 unidades adicionales. Escribe el costo total como suma de dos términos.","8x+48",
         "¿Por qué las formas 8(x+6) y tu suma representan el mismo costo?",
         ("Solo coinciden cuando x vale 6","El precio se aplica a cada grupo de unidades","Las seis unidades adicionales no tienen costo"),1,
         ("Separa los dos grupos de unidades.","Calcula cada costo con la tarifa común."),
         "El costo de x unidades es 8x y el de seis unidades es 48; ambos se suman.",
         (("8x+6","f01-omit"),("8x-48","f01-sign")),"expanded"),
    Item("f01-tutor-inverse","practice_tutor","inverse",
         "Factoriza 18x-12 extrayendo el factor común 6. Usa la forma 6(...).","6(3x-2)",
         "¿Cómo obtienes los términos dentro del paréntesis?",
         ("Divides ambos términos entre 6","Divides solo el término con x","Cambias ambos signos"),0,
         ("Identifica el factor común indicado.","Divide cada término entre 6."),
         "18x/6=3x y -12/6=-2. Al distribuir 6 recuperas el polinomio inicial.",
         (("6(3x-12)","f01-omit"),("6(3x+2)","f01-sign")),"factor6"),
    Item("f01-exam-rational","exam_preparation","rational-identity",
         "Desarrolla (-3/4)(8x-12). Escribe el polinomio sin paréntesis.","-6x+9",
         "¿Por qué el término constante es positivo?",
         ("El producto de dos negativos es positivo","Todo producto con fracciones es positivo","El signo de -12 se elimina sin multiplicar"),0,
         (),
         "(-3/4)(8x)=-6x y (-3/4)(-12)=9.",
         (("-6x-9","f01-sign"),("-6x-12","f01-omit")),"expanded"),
)
INDEX = {i.item_id:i for i in ITEMS}

def _form_ok(item, answer):
    import re
    s = answer.strip().replace("−","-")
    if item.required_form == "expanded":
        # F01 linear expanded form: signed integer/rational monomials and constant.
        return bool(re.fullmatch(r"[+-]?\s*(?:[0-9]+(?:/[0-9]+)?\s*)?x\s*[+-]\s*[0-9]+(?:/[0-9]+)?",s)
                    or re.fullmatch(r"[+-]?\s*[0-9]+(?:/[0-9]+)?\s*[+-]\s*(?:[0-9]+(?:/[0-9]+)?\s*)?x",s))
    if item.required_form == "factor6":
        return bool(re.fullmatch(r"6\s*\([^()]+\)",s))
    return True

def public_item(item_id):
    i = INDEX[item_id]
    return {"item_id":i.item_id,"mode":i.mode,"family":i.family,
            "prompt":i.prompt,"reasoning_prompt":i.reasoning_prompt,"choices":list(i.choices)}

def hint(item_id, index):
    i = INDEX[item_id]
    if i.mode == "exam_preparation":
        raise ValueError("No hints in exam")
    if type(index) is not int or not 0 <= index < len(i.hints):
        raise ValueError("Invalid hint index")
    return {"text":i.hints[index],"assisted":True}

def assess(item_id, answer, reason_choice, assisted=False):
    i = INDEX[item_id]
    if type(assisted) is not bool:
        raise ValueError("assisted must be boolean")
    verdict = compare(answer,i.expected)
    reason_ok = type(reason_choice) is int and reason_choice == i.correct_reason
    diagnostic = None
    accepted = False
    if verdict.status == "INCONCLUSIVE":
        feedback = "No se pudo comprobar la respuesta. Intenta nuevamente; no se registra un error conceptual."
    elif verdict.reason == "INVALID_FORMAT_OR_DOMAIN":
        feedback = "Revisa el formato: usa x, enteros o fracciones y operaciones admitidas. No se infiere una brecha conceptual."
    elif verdict.status == "VERIFIED":
        if not _form_ok(i,answer):
            feedback = "La expresión es equivalente, pero aún no tiene la forma solicitada."
        elif not reason_ok:
            feedback = "La expresión es equivalente. Revisa la justificación de la operación."
        else:
            feedback = i.explanation
            accepted = True
    else:
        for wrong, code in i.errors:
            if compare(answer,wrong).status == "VERIFIED":
                diagnostic = code
                break
        feedback = {"f01-omit":"Revisa si multiplicaste cada sumando por el factor exterior.",
                    "f01-sign":"Revisa la regla de signos de cada producto."}.get(diagnostic,"Compara los coeficientes de cada potencia; revisa la distribución.")
    # Exam feedback must be deferred by the future exam controller. This
    # function is internal only, not a public HTTP endpoint.
    return {"oracle_status":verdict.status,"oracle_reason":verdict.reason,
            "accepted":accepted,"reasoning_correct":reason_ok,"assisted":assisted,
            "eligible_evidence":accepted and not assisted and i.mode!="exam_preparation",
            "diagnostic_hypothesis":diagnostic,"feedback":feedback}
