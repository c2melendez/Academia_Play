"""Original, formative-only worked organizers for M1. Not exam items."""
from copy import deepcopy

ORGANIZERS = {
 "F02": {"title":"Estructura y grado","rule":"Agrupa por exponente. El grado corresponde al mayor exponente cuyo coeficiente reducido no es cero.",
 "columns":["Exponente","Coeficientes","Suma"],"rows":[["3","4, -4","0"],["1","2","2"],["0","-1","-1"]],
 "expression":"4x³ − 4x³ + 2x − 1","question":"¿Qué exponente determina el grado después de reducir?","choices":["3","1","0"],"correct":1,"feedback":"Los cúbicos se cancelan. Queda 2x − 1, de grado 1."},
 "F03": {"title":"Suma y resta","rule":"Alinea los exponentes y distribuye el signo negativo a todo el sustraendo.",
 "columns":["Grado","Primer polinomio","Opuesto del segundo","Suma"],"rows":[["2","3","−1","2"],["1","−2","−4","−6"],["0","1","5","6"]],
 "expression":"(3x² − 2x + 1) − (x² + 4x − 5)","question":"¿Qué coeficiente aporta el término −5 del sustraendo?","choices":["−5","0","5"],"correct":2,"feedback":"Restar −5 equivale a sumar 5. El resultado es 2x² − 6x + 6."},
 "F04": {"title":"Multiplicación","rule":"Cada término de un factor multiplica cada término del otro. La tabla es simbólica, no un área con longitud negativa.",
 "columns":["Factor","x","4"],"rows":[["2x","2x²","8x"],["−3","−3x","−12"]],
 "expression":"(2x − 3)(x + 4)","question":"¿Cuál es la suma de los productos cruzados?","choices":["5x","11x","−5x"],"correct":0,"feedback":"8x − 3x = 5x. El producto reducido es 2x² + 5x − 12."},
 "F05": {"title":"Productos notables","rule":"Para x > 0, un cuadrado de lado x + 2 se descompone en cuatro regiones positivas.",
 "columns":["Dimensión","x","2"],"rows":[["x","x²","2x"],["2","2x","4"]],
 "expression":"(x + 2)²","question":"¿Por qué el término lineal es 4x?","choices":["Se eleva 2x al cuadrado","Hay dos regiones de área 2x","Se suma 2 a x"],"correct":1,"feedback":"Las dos regiones rectangulares suman 4x. El área es x² + 4x + 4."},
 "F06": {"title":"Factorización","rule":"Busca dos factores cuya expansión recupere todos los coeficientes del polinomio.",
 "columns":["Paso","Resultado"],"rows":[["Suma de constantes","−3 − 4 = −7"],["Producto de constantes","(−3)(−4) = 12"],["Producto de binomios","(x − 3)(x − 4)"]],
 "expression":"x² − 7x + 12","question":"¿Qué pareja de constantes permite factorizar en dos binomios mónicos?","choices":["3 y 4","−2 y −6","−3 y −4"],"correct":2,"feedback":"−3 y −4 suman −7 y su producto es 12."},
 "F07": {"title":"División polinómica","rule":"Divide el término principal, multiplica por el divisor y resta. Repite hasta que el residuo sea cero o de grado menor.",
 "columns":["Paso","Cociente parcial","Resta"],"rows":[["1","x","x² + 1 − (x² − x) = x + 1"],["2","1","x + 1 − (x − 1) = 2"]],
 "expression":"(x² + 1) ÷ (x − 1)","question":"¿Por qué termina la división con residuo 2?","choices":["Su grado es menor que el del divisor","El divisor es cero","El residuo debe ser igual al cociente"],"correct":0,"feedback":"El cociente es x + 1 y el residuo 2 tiene grado 0, menor que 1."},
}

def get_organizer(family):
    """Return a fresh public formative representation, not private answer keys."""
    item=deepcopy(ORGANIZERS[family])
    return {k:v for k,v in item.items() if k not in ("correct","feedback")}

def check_prediction(family, choice):
    item=ORGANIZERS[family]
    if type(choice) is not int or not 0<=choice<len(item["choices"]):
        raise ValueError("invalid choice")
    return {"correct":choice==item["correct"],"feedback":item["feedback"],
            "rows":deepcopy(item["rows"]),"assisted":True,"eligible_evidence":False}
