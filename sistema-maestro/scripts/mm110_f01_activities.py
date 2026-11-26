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
    Item("f01-a-sign-positive","learning_path","foundation-sign",
         "Calcula (-3)*(-5). Escribe el resultado como número entero.","15",
         "¿Por qué el resultado tiene ese signo?",
         ("Dos factores negativos producen un positivo","Todo producto es negativo","Se suman los factores"),0,
         ("Compara los signos de ambos factores.","Multiplica sus valores absolutos; signos iguales dan positivo."),
         "Los signos son iguales y 3*5=15; el producto es positivo.",
         (("-15","f01-sign"),),"number"),
    Item("f01-a-fraction-negative","learning_path","foundation-fraction",
         "Calcula (-2/3)*(9/4). Escribe una fracción equivalente al resultado.","-3/2",
         "¿Cómo se determina el producto?",
         ("Se suman numeradores y denominadores","Se multiplican numeradores y denominadores; signos distintos dan negativo","Se cambia el signo a positivo"),1,
         ("Determina primero el signo.","Multiplica 2 por 9 y 3 por 4; simplifica."),
         "El producto es -18/12=-3/2, porque los factores tienen signos distintos.",
         (("3/2","f01-sign"),),"number"),
    Item("f01-b-predict","learning_path","foundation-prediction",
         "Antes de ver el resultado, predice la suma que representa 4 grupos de x+3 unidades.","4x+12",
         "¿Qué productos representan los dos grupos de términos?",
         ("4*x y 3","x y 4*3","4*x y 4*3"),2,
         ("Identifica las dos cantidades dentro de cada grupo.","Multiplica cada cantidad por 4."),
         "Cada uno de los cuatro grupos aporta x y 3 unidades: 4x+12.",
         (("4x+3","f01-omit"),),"expanded"),
    Item("f01-b-group","learning_path","foundation-grouping",
         "Calcula 4(2+5) y escribe su valor entero.","28",
         "¿Cuál es una descomposición equivalente?",
         ("4*2+5","4*2+4*5","4+2+5"),1,
         ("Cuenta los elementos en cuatro grupos de siete.","Distribuye 4 sobre 2 y sobre 5."),
         "Cuatro grupos de siete contienen 28 elementos; 8+20=28.",
         (("13","f01-omit"),),"number"),
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
    Item("f01-transfer-perimeter","learning_path","contextual",
         "Un rectángulo mide x+5 metros de largo y 3 metros de ancho. Escribe su perímetro como suma de dos términos.","2x+16",
         "¿Por qué se multiplica por 2 la suma de largo y ancho?",
         ("Porque hay dos lados de cada longitud","Porque se calcula el área","Porque solo se cuentan los lados largos"),0,
         ("Recuerda qué mide el perímetro.","Suma las cuatro longitudes y agrupa términos."),
         "El perímetro es 2(x+5)+2(3)=2x+16 metros.",
         (("2x+8","f01-omit"),("2x+10","f01-omit")),"expanded"),
    Item("f01-transfer-discount","learning_path","contextual",
         "Una tienda aplica un descuento de la cuarta parte al precio de un paquete de x lempiras más un accesorio de 12 lempiras. Escribe el importe final como suma de dos términos.","3/4x+9",
         "¿Qué parte del precio original paga el cliente?",
         ("Una cuarta parte","Tres cuartas partes de ambos componentes","Tres cuartas partes únicamente del paquete"),1,
         ("Si se descuenta 1/4, ¿qué fracción permanece?","Aplica esa fracción al precio total."),
         "Se paga 3/4 del total: (3/4)(x+12)=3/4x+9.",
         (("3/4x+12","f01-omit"),("1/4x+3","f01-identity")),"expanded"),
    Item("f01-transfer-balance","learning_path","contextual",
         "Una cuenta recibe tres cargos idénticos de x+4 lempiras. Representa el cambio de saldo como expresión desarrollada, usando signo negativo para los cargos.","-3x-12",
         "¿Cómo se representa una disminución repetida del saldo?",
         ("Se suma tres veces el importe positivo","Se resta solamente el importe variable","Se multiplica todo el importe por -3"),2,
         ("Un cargo disminuye el saldo.","Representa tres disminuciones iguales y distribuye el factor."),
         "Los cargos reducen el saldo en -3(x+4)=-3x-12 lempiras.",
         (("-3x+12","f01-sign"),("-3x-4","f01-omit")),"expanded"),
    Item("f01-transfer-reserve-fuel","learning_path","contextual",
         "Un motor consume 2 litros por hora. Funciona x horas por la mañana y media hora por la tarde. Escribe el consumo total como suma de dos términos.","2x+1",
         "¿Qué representa el término constante?",
         ("El consumo de media hora","El consumo de dos horas","El número de horas de la mañana"),0,
         ("La tasa se aplica a ambos tiempos.","Multiplica 2 por 1/2."),
         "El consumo total es 2(x+1/2)=2x+1 litros.",
         (("2x+2","f01-omit"),),"expanded"),
    Item("f01-transfer-reserve-temperature","learning_path","contextual",
         "Durante cada uno de cuatro intervalos, la temperatura baja x+2 grados. Escribe la variación total de temperatura como suma de dos términos.","-4x-8",
         "¿Por qué el factor exterior es negativo?",
         ("Porque x siempre es negativo","Porque una disminución se representa con signo negativo","Porque la temperatura final siempre es negativa"),1,
         ("Distingue la variación de la temperatura final.","Multiplica ambos sumandos por -4."),
         "La variación es -4(x+2)=-4x-8 grados.",
         (("-4x+8","f01-sign"),),"expanded"),
    Item("f01-transfer-reserve-scale","learning_path","contextual",
         "Una maqueta representa a escala 1/5 una longitud real de 10x+15 centímetros. Escribe la longitud de la maqueta como suma de dos términos.","2x+3",
         "¿Cómo se aplica la escala a la longitud?",
         ("Solo al término constante","Solo al término variable","A la longitud completa"),2,
         ("La escala divide toda la longitud entre cinco.","Divide cada término entre cinco."),
         "La longitud de la maqueta es (10x+15)/5=2x+3 centímetros.",
         (("2x+15","f01-omit"),),"expanded"),
    Item("f01-transfer-reserve-sharing","learning_path","contextual",
         "Tres grupos reciben cantidades iguales de material. En total hay 6x-9 unidades, con x entero mayor o igual que 2. Escribe la cantidad de cada grupo como suma de dos términos.","2x-3",
         "¿Qué operación corresponde al reparto equitativo?",
         ("Dividir ambos términos entre tres","Restar tres al total","Dividir únicamente el término variable"),0,
         ("La cantidad total se reparte entre tres grupos.","Divide cada término entre tres."),
         "Cada grupo recibe (6x-9)/3=2x-3 unidades.",
         (("2x-9","f01-omit"),("2x+3","f01-sign")),"expanded"),
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
    if item.required_form == "number":
        return bool(re.fullmatch(r"[+-]?[0-9]+(?:/[0-9]+)?",s))
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
                    "f01-sign":"Revisa la regla de signos de cada producto."}.get(diagnostic,"Revisa los productos y las operaciones indicadas.")
    # Exam feedback must be deferred by the future exam controller. This
    # function is internal only, not a public HTTP endpoint.
    return {"oracle_status":verdict.status,"oracle_reason":verdict.reason,
            "accepted":accepted,"reasoning_correct":reason_ok,"assisted":assisted,
            "eligible_evidence":accepted and not assisted and i.mode!="exam_preparation" and not i.family.startswith("foundation-"),
            "diagnostic_hypothesis":diagnostic,"feedback":feedback}
