"""Arma el informe, el cuaderno de Colab y el libro de Excel a partir de la simulación."""

import json
from pathlib import Path

import matplotlib
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

matplotlib.use("Agg")

import hmm_mercado_financiero as hmm

CARPETA = Path(__file__).resolve().parent
NOMBRE_BASE = "Ramirez_Paul_Markov"


def pct(valor, decimales=1):
    if valor is None:
        return "—"
    texto = f"{valor * 100:.{decimales}f}"
    return texto.replace(".", ",") + " %"


def num(valor, decimales=2):
    if valor is None:
        return "—"
    return f"{valor:.{decimales}f}".replace(".", ",")


def fila_matriz(valores, decimales=1):
    return " | ".join(num(v, decimales) for v in valores)


def sombrear_celda(celda, color):
    celda.paragraphs[0].runs[0].font.bold = True
    celda.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    sombreado = OxmlElement("w:shd")
    sombreado.set(qn("w:fill"), color)
    sombreado.set(qn("w:val"), "clear")
    celda._tc.get_or_add_tcPr().append(sombreado)


def agregar_parrafo(doc, texto):
    parrafo = doc.add_paragraph(texto)
    parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    parrafo.paragraph_format.space_after = Pt(8)
    parrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    parrafo.paragraph_format.line_spacing = 1.15
    return parrafo


def agregar_tabla(doc, encabezados, filas):
    tabla = doc.add_table(rows=1, cols=len(encabezados))
    tabla.style = "Table Grid"
    for i, titulo in enumerate(encabezados):
        tabla.rows[0].cells[i].text = titulo
        sombrear_celda(tabla.rows[0].cells[i], "1F4E79")
    for fila in filas:
        celdas = tabla.add_row().cells
        for i, valor in enumerate(fila):
            celdas[i].text = str(valor)
    doc.add_paragraph()
    return tabla


def configurar_estilos(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    for nivel in (1, 2):
        estilo = doc.styles[f"Heading {nivel}"]
        estilo.font.name = "Times New Roman"
        estilo.font.color.rgb = RGBColor(31, 78, 121)
        estilo.font.bold = True
        estilo._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    seccion = doc.sections[0]
    seccion.top_margin = Cm(2.5)
    seccion.bottom_margin = Cm(2.5)
    seccion.left_margin = Cm(2.5)
    seccion.right_margin = Cm(2.5)


def construir_informe(resultado):
    principal = resultado["principal"]
    modelo = resultado["modelo"]
    estacionaria = resultado["estacionaria"]
    duracion = resultado["duracion_teorica"]
    validacion = resultado["validacion"]
    texto_rec, texto_riesgo = hmm.recomendacion(principal["estado_final"], principal)

    doc = Document()
    configurar_estilos(doc)

    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run("IU Digital\n")
    run.bold = True
    run.font.size = Pt(14)
    run.font.name = "Times New Roman"
    sub = titulo.add_run("Simulación — Semestre V\n\n")
    sub.font.size = Pt(12)
    sub.font.name = "Times New Roman"
    principal_run = titulo.add_run(
        "Modelo oculto de Markov aplicado a regímenes\nde mercado financiero\n"
    )
    principal_run.bold = True
    principal_run.font.size = Pt(18)
    principal_run.font.name = "Times New Roman"
    meta = titulo.add_run("\nPaul Ramirez\n31 de octubre de 2026")
    meta.font.size = Pt(12)
    meta.font.name = "Times New Roman"

    doc.add_heading("Introducción", level=1)
    agregar_parrafo(
        doc,
        "Un mercado no muestra su régimen. Lo que se observa cada período es un retorno: "
        "positivo, cercano a cero o negativo. Detrás de esa cifra puede haber un mercado "
        "alcista, uno lateral o uno bajista, y el régimen de mañana depende sobre todo del "
        "régimen de hoy. Esa es la estructura de un modelo oculto de Markov (HMM): una cadena "
        "de estados que no se ve, y una observación que sí se ve y que depende del estado vigente.",
    )
    agregar_parrafo(
        doc,
        "El objetivo de este trabajo es aplicar distribuciones de probabilidad a un HMM que se "
        "pueda ejecutar y que, al cambiar la semilla del generador aleatorio, produzca escenarios "
        "distintos. El caso elegido es el análisis de mercado financiero. Se simulan 50 períodos "
        "de trading, se construye un precio a partir de los retornos y se leen duración de los "
        "regímenes, retorno acumulado, volatilidad, drawdown, cambios de régimen, una recomendación "
        "ligada al régimen final y una lectura de riesgo.",
    )
    agregar_parrafo(
        doc,
        "Entran dos familias de distribuciones. La distribución categórica elige el estado inicial, "
        "el estado siguiente y la etiqueta del retorno. La distribución uniforme elige el tamaño del "
        "retorno dentro de un intervalo que depende del estado y de esa etiqueta. La duración de cada "
        "visita a un régimen sigue una distribución geométrica: si la probabilidad de quedarse es p, "
        "la duración esperada es 1 / (1 − p).",
    )
    agregar_parrafo(
        doc,
        "El alcance es didáctico. Las matrices no se estimaron con precios de un activo real; son las "
        "del enunciado. El resultado no es una recomendación de inversión. Sirve para ver cómo un "
        "mismo mecanismo probabilístico genera trayectorias distintas y cómo, a partir de los retornos "
        "observados, se puede recuperar una secuencia probable de regímenes.",
    )

    doc.add_heading("Metodología", level=1)
    doc.add_heading("Componentes del modelo", level=2)
    agregar_parrafo(
        doc,
        "El HMM queda definido por cinco elementos. Los estados ocultos son Mercado Alcista, "
        "Mercado Lateral y Mercado Bajista. Las observaciones son Retorno Positivo, Retorno Neutral "
        "y Retorno Negativo. La distribución inicial π da la probabilidad del régimen en el período 1. "
        "La matriz de transición A da P(estado de mañana | estado de hoy). La matriz de emisión B da "
        "P(observación | estado). Cada fila de A, cada fila de B y el vector π son distribuciones "
        "categóricas: sus valores son no negativos y suman 1. El programa rechaza la especificación "
        "si esa condición falla.",
    )
    agregar_parrafo(doc, "Distribución inicial π:")
    agregar_tabla(
        doc,
        ["Alcista", "Lateral", "Bajista"],
        [["0,40", "0,30", "0,30"]],
    )
    agregar_parrafo(
        doc,
        "La matriz de transición refleja persistencia. Un mercado alcista sigue alcista con "
        "probabilidad 0,60, pasa a lateral con 0,30 y cae directo a bajista con 0,10. El bajista "
        "es simétrico: se queda con 0,60 y sale hacia alcista solo con 0,10. El lateral es el "
        "estado puente: se queda con 0,40 y reparte el resto en partes iguales. Por la propiedad "
        "de Markov, el régimen futuro depende del régimen presente y no de la trayectoria anterior.",
    )
    agregar_tabla(
        doc,
        ["Desde \\ hacia", "Alcista", "Lateral", "Bajista"],
        [
            ["Alcista", "0,60", "0,30", "0,10"],
            ["Lateral", "0,30", "0,40", "0,30"],
            ["Bajista", "0,10", "0,30", "0,60"],
        ],
    )
    agregar_parrafo(
        doc,
        "La matriz de emisión hace que la observación sea una señal ruidosa del régimen. En un "
        "mercado alcista el retorno positivo es lo habitual (0,70), pero todavía puede salir "
        "neutral (0,20) o negativo (0,10). En el bajista la masa está en el retorno negativo (0,70). "
        "En el lateral las tres etiquetas son parecidas, con un poco más de peso en el retorno "
        "neutral (0,40). Por eso un día negativo no demuestra, por sí solo, que el régimen sea bajista.",
    )
    agregar_tabla(
        doc,
        ["Estado \\ observación", "Positivo", "Neutral", "Negativo"],
        [
            ["Alcista", "0,70", "0,20", "0,10"],
            ["Lateral", "0,30", "0,40", "0,30"],
            ["Bajista", "0,10", "0,20", "0,70"],
        ],
    )

    doc.add_heading("Algoritmo de simulación", level=2)
    agregar_parrafo(
        doc,
        "Para cada escenario se fija una semilla del generador de NumPy, de modo que el mismo "
        "escenario se pueda repetir y otra semilla produzca otro camino. El algoritmo es el siguiente.",
    )
    pasos = [
        "Se sortea el estado del período 1 con la distribución π.",
        "Se sortea la observación de ese período con la fila correspondiente de B.",
        "Se sortea la magnitud del retorno con una uniforme en el intervalo del par (estado, observación). El intervalo conserva el signo de la etiqueta: un retorno positivo cae entre un piso y un techo positivos.",
        "El precio arranca en 100. Al cierre del período t vale el precio anterior multiplicado por (1 + retorno del período).",
        "Del período 2 al 50, el estado nuevo se sortea con la fila de A del estado anterior, y se repiten la observación, la magnitud y la actualización del precio.",
    ]
    for paso in pasos:
        doc.add_paragraph(paso, style="List Number")
    agregar_parrafo(
        doc,
        "La magnitud no sale de B. B solo elige la etiqueta. El tamaño sale de una uniforme "
        "condicional, más amplia en los extremos del régimen bajista y más estrecha en el lateral. "
        "Así la volatilidad puede diferir entre regímenes aunque la cadena sea la misma. Los "
        "intervalos usados son: alcista-positivo [0,6 %, 2,8 %], alcista-neutral [−0,2 %, 0,4 %], "
        "alcista-negativo [−1,5 %, −0,3 %], lateral-positivo [0,3 %, 1,2 %], lateral-neutral "
        "[−0,4 %, 0,4 %], lateral-negativo [−1,2 %, −0,3 %], bajista-positivo [0,3 %, 1,0 %], "
        "bajista-neutral [−0,5 %, 0,2 %] y bajista-negativo [−3,2 %, −0,6 %].",
    )

    doc.add_heading("Duración, distribución estacionaria y decodificación", level=2)
    agregar_parrafo(
        doc,
        "Si un régimen se queda consigo mismo con probabilidad p, el número de períodos que dura "
        "una visita es geométrico y su esperanza es 1 / (1 − p). Con las diagonales del enunciado, "
        f"la duración esperada es {num(duracion[0], 2)} períodos en alcista, {num(duracion[1], 2)} "
        f"en lateral y {num(duracion[2], 2)} en bajista. Una simulación de 50 períodos es corta "
        "frente a esas medias: las duraciones observadas van a moverse alrededor de la teoría, "
        "no a copiarla.",
    )
    agregar_parrafo(
        doc,
        "A largo plazo la proporción de tiempo en cada régimen deja de depender de π y converge "
        "a la distribución estacionaria, la solución de π = π A con componentes que suman 1. "
        f"En este modelo esa distribución es {pct(estacionaria[0])} alcista, "
        f"{pct(estacionaria[1])} lateral y {pct(estacionaria[2])} bajista. Para comprobar que el "
        f"generador respeta A y B se corrió una cadena de {hmm.N_VALIDACION} períodos, aparte de "
        "los escenarios de 50.",
    )
    agregar_parrafo(
        doc,
        "En la simulación el estado se conoce porque lo genera el programa. En un mercado real "
        "solo se verían los retornos. Para ese problema se implementó el algoritmo de Viterbi: "
        "recorre la serie de observaciones y devuelve la secuencia de regímenes con mayor "
        "probabilidad conjunta. El cálculo se hace en logaritmos para no desbordar el producto "
        "de 50 probabilidades. Esa secuencia se compara con los estados simulados y el porcentaje "
        "de coincidencias mide cuánta información conserva la observación ruidosa.",
    )

    doc.add_heading("Métricas, gráficos y escenarios", level=2)
    agregar_parrafo(
        doc,
        "Sobre la trayectoria de 50 períodos se calculan la duración media de cada régimen "
        "(promedio de las rachas consecutivas), el retorno acumulado del precio, la desviación "
        "estándar de los retornos diarios dentro de cada régimen, y el drawdown máximo: la peor "
        "caída desde un máximo previo hasta un cierre posterior. Un cambio de régimen es cualquier "
        "período cuyo estado difiere del anterior. La recomendación usa solo el régimen del último "
        "período y las probabilidades de la fila correspondiente de A. El análisis de riesgo junta "
        "el drawdown, el peor día y el número de cambios.",
    )
    agregar_parrafo(
        doc,
        "El escenario que se desarrolla en el informe usa la semilla 42. Otras cuatro semillas "
        "(7, 21, 99 y 2026) muestran que la misma especificación no produce el mismo mercado. "
        "Los gráficos del escenario principal son la línea de precio con fondo verde, amarillo o "
        "rojo según el régimen, y las barras de retorno coloreadas según la observación.",
    )

    doc.add_heading("Resultados y conclusiones", level=1)
    doc.add_heading("Comprobación del generador", level=2)
    agregar_parrafo(
        doc,
        f"En {hmm.N_VALIDACION} períodos la frecuencia de estados fue "
        f"{pct(validacion['frec_estados'][0])} alcista, "
        f"{pct(validacion['frec_estados'][1])} lateral y "
        f"{pct(validacion['frec_estados'][2])} bajista, frente a la estacionaria teórica de "
        f"{pct(estacionaria[0])}, {pct(estacionaria[1])} y {pct(estacionaria[2])}. "
        "Las frecuencias de transición y de emisión quedan cerca de A y de B. La diferencia que "
        "queda es el error de una muestra finita, no un sesgo del algoritmo.",
    )
    agregar_tabla(
        doc,
        ["", "Alcista", "Lateral", "Bajista"],
        [[
            "Estacionaria teórica",
            pct(estacionaria[0]),
            pct(estacionaria[1]),
            pct(estacionaria[2]),
        ], [
            f"Frecuencia en {hmm.N_VALIDACION} períodos",
            pct(validacion["frec_estados"][0]),
            pct(validacion["frec_estados"][1]),
            pct(validacion["frec_estados"][2]),
        ]],
    )
    filas_a = []
    for i, nombre in enumerate(hmm.ETIQUETAS_CORTAS):
        filas_a.append([nombre] + [num(v, 2) for v in validacion["transicion"][i]])
    agregar_parrafo(doc, "Frecuencias de transición estimadas en la cadena larga (cada fila suma 1):")
    agregar_tabla(doc, ["Desde \\ hacia", "Alcista", "Lateral", "Bajista"], filas_a)
    filas_b = []
    for i, nombre in enumerate(hmm.ETIQUETAS_CORTAS):
        filas_b.append([nombre] + [num(v, 2) for v in validacion["emision"][i]])
    agregar_parrafo(doc, "Frecuencias de emisión estimadas en la cadena larga:")
    agregar_tabla(doc, ["Estado \\ observación", "Positivo", "Neutral", "Negativo"], filas_b)

    doc.add_heading("Escenario de 50 períodos (semilla 42)", level=2)
    agregar_parrafo(
        doc,
        f"El precio parte de {num(hmm.PRECIO_INICIAL, 2)} y cierra en {num(principal['precio_final'], 2)}. "
        f"El retorno acumulado es {pct(principal['retorno_total'])}. El mejor día rindió "
        f"{pct(principal['mejor_retorno'])} y el peor {pct(principal['peor_retorno'])}. "
        f"El drawdown máximo fue {pct(principal['drawdown_maximo'])}. "
        f"El régimen final es {hmm.ESTADOS[principal['estado_final']]}. "
        f"Viterbi, usando solo la etiqueta del retorno, coincidió con el estado simulado en "
        f"{pct(principal['acierto_viterbi'], 1)} de los períodos. Elegir siempre el mismo régimen "
        "acertaría cerca de un tercio, porque la distribución estacionaria es uniforme. El margen "
        "por encima de eso es la información que conserva B. No es una reconstrucción completa: "
        "un retorno positivo también puede salir de un mercado lateral o bajista, y las visitas "
        "duran pocos períodos.",
    )

    filas_reg = []
    for i, nombre in enumerate(hmm.ESTADOS):
        dur_obs = principal["duracion_promedio"][i]
        vol = principal["volatilidad"][i]
        filas_reg.append([
            nombre,
            str(principal["dias_por_regimen"][i]),
            num(duracion[i], 2),
            num(dur_obs, 2) if dur_obs is not None else "—",
            pct(vol, 2) if vol is not None else "—",
        ])
    agregar_tabla(
        doc,
        ["Régimen", "Períodos", "Duración esperada", "Duración media observada", "Volatilidad diaria"],
        filas_reg,
    )
    vol = principal["volatilidad"]
    agregar_parrafo(
        doc,
        "La duración observada no replica la esperanza teórica porque 50 períodos alcanzan para "
        f"pocas rachas. En esta corrida la volatilidad diaria fue {pct(vol[0], 2)} en alcista, "
        f"{pct(vol[1], 2)} en lateral y {pct(vol[2], 2)} en bajista. El lateral usa intervalos "
        "más estrechos y queda por debajo. Alcista y bajista salen parejos en esta muestra, aunque "
        "el intervalo del retorno negativo en mercado bajista sea el más ancho: con pocos días, "
        "esa desviación cambia de una semilla a otra. Si un régimen aparece menos de dos veces, "
        "la desviación estándar no se calcula.",
    )

    if principal["cambios"]:
        filas_c = [
            [str(c["periodo"]), c["desde"], c["hacia"]]
            for c in principal["cambios"]
        ]
        agregar_parrafo(
            doc,
            f"Se identificaron {principal['n_cambios']} cambios de régimen. El número de período "
            "es la sesión en la que el estado nuevo ya está vigente.",
        )
        agregar_tabla(doc, ["Período", "Desde", "Hacia"], filas_c)
    else:
        agregar_parrafo(doc, "En este escenario el régimen no cambió.")

    doc.add_picture(str(CARPETA / "figuras" / "precio_regimenes.png"), width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    pie = doc.add_paragraph("Figura 1. Precio simulado. El fondo marca el régimen: verde alcista, amarillo lateral, rojo bajista.")
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in pie.runs:
        run.italic = True
        run.font.size = Pt(11)

    doc.add_picture(str(CARPETA / "figuras" / "retornos_observados.png"), width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    pie = doc.add_paragraph("Figura 2. Retorno de cada período. Verde positivo, gris neutral, rojo negativo.")
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in pie.runs:
        run.italic = True
        run.font.size = Pt(11)

    doc.add_heading("Cinco resultados con la misma especificación", level=2)
    agregar_parrafo(
        doc,
        "Cambiar la semilla no cambia A, B ni π. Cambia la secuencia que esas distribuciones "
        "sortean. Por eso el retorno acumulado, el drawdown y el régimen de cierre no coinciden "
        "entre corridas. Esa dispersión es el resultado que el modelo debe poder mostrar.",
    )
    filas_cmp = []
    for fila in resultado["comparacion"]:
        filas_cmp.append([
            str(fila["semilla"]),
            num(fila["precio_final"], 2),
            pct(fila["retorno_total"]),
            pct(fila["drawdown_maximo"]),
            str(fila["n_cambios"]),
            hmm.ESTADOS[fila["estado_final"]],
            pct(fila["acierto_viterbi"], 0),
        ])
    agregar_tabla(
        doc,
        ["Semilla", "Precio final", "Retorno", "Drawdown máximo", "Cambios", "Régimen final", "Acierto Viterbi"],
        filas_cmp,
    )
    doc.add_picture(str(CARPETA / "figuras" / "comparacion_escenarios.png"), width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    pie = doc.add_paragraph("Figura 3. Retorno acumulado de las cinco simulaciones.")
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in pie.runs:
        run.italic = True
        run.font.size = Pt(11)

    doc.add_heading("Recomendación y riesgo del escenario principal", level=2)
    agregar_parrafo(doc, texto_rec)
    agregar_parrafo(doc, texto_riesgo)
    agregar_parrafo(
        doc,
        "La recomendación no usa un pronóstico de precio. Usa la fila de A del régimen vigente: "
        "la probabilidad de quedarse, la de pasar al régimen vecino y la de saltar al extremo "
        "opuesto. Si el próximo retorno contradice esa fila, el régimen inferido puede cambiar "
        "en el período siguiente. Por eso la regla va atada a un límite de pérdida y no a una "
        "posición fija durante los 50 períodos.",
    )

    doc.add_heading("Conclusiones", level=2)
    retornos = [fila["retorno_total"] for fila in resultado["comparacion"]]
    agregar_parrafo(
        doc,
        "El modelo se puede ejecutar y produce escenarios distintos sin modificar las "
        "distribuciones. En las cinco semillas el retorno acumulado fue desde "
        f"{pct(min(retornos))} hasta {pct(max(retornos))}. Esa amplitud sale de la categórica "
        "de los regímenes y de la uniforme de las magnitudes, no de un cambio de parámetros.",
    )
    agregar_parrafo(
        doc,
        "La cadena larga confirma que el generador reproduce la distribución estacionaria, la "
        "matriz de transición y la matriz de emisión. En la ventana corta de 50 períodos las "
        "duraciones observadas se apartan de la esperanza geométrica, como corresponde a una "
        "muestra pequeña. Viterbi supera a elegir un régimen al azar, y al mismo tiempo deja "
        "ver el límite del modelo: la emisión está hecha para equivocarse y las visitas son cortas, "
        "así que una parte de los días queda mal clasificada.",
    )
    agregar_parrafo(
        doc,
        "La lectura financiera cabe en tres ideas. Los regímenes persisten, así que un día no "
        "basta para declararlos terminados. La observación es ruidosa, así que un retorno "
        "negativo puede ocurrir en un mercado alcista. Y el riesgo relevante de estos caminos "
        "no es solo el retorno final: es el drawdown acumulado entre el máximo y el cierre "
        "posterior, y la cantidad de cambios de régimen en los que una regla llega tarde.",
    )
    agregar_parrafo(
        doc,
        "La limitación principal es que A, B y los intervalos de retorno están dados, no estimados "
        "con un histórico. Un paso siguiente sería calibrar esas distribuciones con retornos reales "
        "y volver a correr la misma simulación. Mientras eso no se haga, las cifras de este informe "
        "describen el mecanismo del enunciado, no un activo concreto. Nada de lo anterior constituye "
        "asesoría de inversión.",
    )

    doc.add_heading("Referencia de implementación", level=2)
    agregar_parrafo(
        doc,
        "El algoritmo está en hmm_mercado_financiero.py y en el cuaderno "
        "hmm_mercado_financiero.ipynb, ejecutable en Google Colab. La serie del escenario "
        "principal está en datos/escenario_principal.csv y en Ramirez_Paul_Markov_datos.xlsx. "
        "Para obtener otro mercado basta con cambiar SEMILLA_PRINCIPAL y volver a ejecutar el archivo.",
    )

    destino = CARPETA / f"{NOMBRE_BASE}.docx"
    doc.save(destino)
    return destino


def crear_excel(resultado):
    principal = resultado["principal"]
    libro = Workbook()
    encabezado = Font(bold=True, color="FFFFFF")
    relleno = PatternFill("solid", fgColor="1F4E79")
    centro = Alignment(horizontal="center")

    def pintar(hoja, fila, columnas):
        for col in range(1, columnas + 1):
            celda = hoja.cell(fila, col)
            celda.font = encabezado
            celda.fill = relleno
            celda.alignment = centro

    parametros = libro.active
    parametros.title = "Parametros"
    parametros["A1"] = "Elemento"
    parametros["B1"] = "Alcista"
    parametros["C1"] = "Lateral"
    parametros["D1"] = "Bajista"
    pintar(parametros, 1, 4)
    parametros["A2"] = "Distribución inicial"
    for col, valor in enumerate(hmm.PI, start=2):
        parametros.cell(2, col, float(valor))
    parametros["A4"] = "Matriz de transición"
    for i, nombre in enumerate(hmm.ETIQUETAS_CORTAS):
        parametros.cell(5 + i, 1, nombre)
        for j, valor in enumerate(hmm.A[i]):
            parametros.cell(5 + i, 2 + j, float(valor))
    parametros["A9"] = "Matriz de emisión"
    parametros["B9"] = "Positivo"
    parametros["C9"] = "Neutral"
    parametros["D9"] = "Negativo"
    pintar(parametros, 9, 4)
    for i, nombre in enumerate(hmm.ETIQUETAS_CORTAS):
        parametros.cell(10 + i, 1, nombre)
        for j, valor in enumerate(hmm.B[i]):
            parametros.cell(10 + i, 2 + j, float(valor))
    parametros["A14"] = "Períodos"
    parametros["B14"] = hmm.N_PERIODOS
    parametros["A15"] = "Precio inicial"
    parametros["B15"] = hmm.PRECIO_INICIAL
    parametros["A16"] = "Semilla del escenario principal"
    parametros["B16"] = hmm.SEMILLA_PRINCIPAL
    for col in range(1, 5):
        parametros.column_dimensions[get_column_letter(col)].width = 28

    serie = libro.create_sheet("Simulacion")
    columnas = ["Periodo", "Estado", "Estado Viterbi", "Observacion", "Retorno", "Precio de cierre"]
    for col, titulo in enumerate(columnas, start=1):
        serie.cell(1, col, titulo)
    pintar(serie, 1, len(columnas))
    for t in range(hmm.N_PERIODOS):
        serie.cell(t + 2, 1, t + 1)
        serie.cell(t + 2, 2, hmm.ESTADOS[int(principal["estados"][t])])
        serie.cell(t + 2, 3, hmm.ESTADOS[int(principal["viterbi"][t])])
        serie.cell(t + 2, 4, hmm.OBSERVACIONES[int(principal["obs"][t])])
        serie.cell(t + 2, 5, float(principal["retornos"][t]))
        serie.cell(t + 2, 6, float(principal["precios"][t + 1]))
        serie.cell(t + 2, 5).number_format = "0.00%"
        serie.cell(t + 2, 6).number_format = "0.00"
    for col in range(1, 7):
        serie.column_dimensions[get_column_letter(col)].width = 24

    metricas = libro.create_sheet("Metricas")
    metricas["A1"] = "Métrica"
    metricas["B1"] = "Valor"
    pintar(metricas, 1, 2)
    filas = [
        ("Precio final", principal["precio_final"]),
        ("Retorno acumulado", principal["retorno_total"]),
        ("Drawdown máximo", principal["drawdown_maximo"]),
        ("Cambios de régimen", principal["n_cambios"]),
        ("Acierto de Viterbi", principal["acierto_viterbi"]),
        ("Mejor retorno diario", principal["mejor_retorno"]),
        ("Peor retorno diario", principal["peor_retorno"]),
    ]
    for i, (nombre, valor) in enumerate(filas, start=2):
        metricas.cell(i, 1, nombre)
        metricas.cell(i, 2, valor)
    metricas.column_dimensions["A"].width = 28
    metricas.column_dimensions["B"].width = 18

    escenarios = libro.create_sheet("Escenarios")
    cabeceras = ["Semilla", "Precio final", "Retorno", "Drawdown máximo", "Cambios", "Régimen final", "Acierto Viterbi"]
    for col, titulo in enumerate(cabeceras, start=1):
        escenarios.cell(1, col, titulo)
    pintar(escenarios, 1, len(cabeceras))
    for i, fila in enumerate(resultado["comparacion"], start=2):
        escenarios.cell(i, 1, fila["semilla"])
        escenarios.cell(i, 2, fila["precio_final"])
        escenarios.cell(i, 3, fila["retorno_total"])
        escenarios.cell(i, 4, fila["drawdown_maximo"])
        escenarios.cell(i, 5, fila["n_cambios"])
        escenarios.cell(i, 6, hmm.ESTADOS[fila["estado_final"]])
        escenarios.cell(i, 7, fila["acierto_viterbi"])
        escenarios.cell(i, 3).number_format = "0.00%"
        escenarios.cell(i, 4).number_format = "0.00%"
        escenarios.cell(i, 7).number_format = "0.00%"
    for col in range(1, 8):
        escenarios.column_dimensions[get_column_letter(col)].width = 22

    destino = CARPETA / f"{NOMBRE_BASE}_datos.xlsx"
    libro.save(destino)
    return destino


def crear_cuaderno():
    fuente = (CARPETA / "hmm_mercado_financiero.py").read_text(encoding="utf-8")
    nb = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "colab": {"provenance": []},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# HMM de regímenes de mercado financiero\n",
                    "\n",
                    "Paul Ramirez — Simulación, Semestre V, IU Digital.\n",
                    "\n",
                    "Estados ocultos: Mercado Alcista, Mercado Lateral y Mercado Bajista.  \n",
                    "Observaciones: Retorno Positivo, Retorno Neutral y Retorno Negativo.\n",
                    "\n",
                    "Ejecuta el cuaderno completo en Google Colab. Para otro escenario, cambia `SEMILLA_PRINCIPAL`.\n",
                ],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": fuente.splitlines(keepends=True),
            },
        ],
    }
    destino = CARPETA / "hmm_mercado_financiero.ipynb"
    destino.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino


def main():
    resultado = hmm.main()
    informe = construir_informe(resultado)
    excel = crear_excel(resultado)
    cuaderno = crear_cuaderno()
    print()
    print(f"Informe: {informe}")
    print(f"Excel:   {excel}")
    print(f"Cuaderno: {cuaderno}")


if __name__ == "__main__":
    main()
