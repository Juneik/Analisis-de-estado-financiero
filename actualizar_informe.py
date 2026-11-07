"""Actualiza el informe del equipo con las cifras que produce el programa."""

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

CARPETA = Path(__file__).resolve().parent
INFORME = CARPETA / "Pieschacon_Camilo_Tirado_Paul_Buitrago_MariaFernanda.docx"

REFERENCIAS_NUEVAS = [
    '[12] J. Liu, J. M. Maheu, and Y. Song, "Identification and forecasting of bull and bear markets using multivariate returns," Journal of Applied Econometrics, vol. 39, no. 5, pp. 723–745, 2024, doi: 10.1002/jae.3048.',
    '[13] J. Wang, M. Zhou, X. Guo, L. Qi, and X. Wang, "A Markov regime switching model for asset pricing and ambiguity measurement of stock market," Neurocomputing, vol. 435, pp. 283–294, 2021, doi: 10.1016/j.neucom.2020.12.103.',
    '[14] N. Naik and B. R. Mohan, "Stock price volatility estimation using regime switching technique-empirical study on the Indian stock market," Mathematics, vol. 9, no. 14, art. 1595, 2021, doi: 10.3390/math9141595.',
    '[15] M. Mahmoudi and H. Ghaneei, "Detection of structural regimes and analyzing the impact of crude oil market on Canadian stock market: Markov regime-switching approach," Studies in Economics and Finance, vol. 39, no. 4, pp. 722–734, 2022, doi: 10.1108/SEF-09-2021-0352.',
    '[16] S. K. Chavoshi, A. Mansouri, and S. Sheidani, "An improvement of hidden Markov model for stock market predictions," International Journal of Reasoning-based Intelligent Systems, vol. 14, no. 2/3, p. 144, 2022, doi: 10.1504/IJRIS.2022.125433.',
    '[17] S. A. Athari, D. Kirikkaleli, and T. S. Adebayo, "World pandemic uncertainty and German stock market: evidence from Markov regime-switching and Fourier based approaches," Quality & Quantity, vol. 57, no. 2, pp. 1923–1936, 2023, doi: 10.1007/s11135-022-01435-4.',
    '[18] I. A. Raifu and S. O. Oshota, "Re-examining oil price-stock market returns nexus in Nigeria using a two-stage Markov regime switching approach," International Journal of Energy Sector Management, vol. 17, no. 3, pp. 489–509, 2023, doi: 10.1108/IJESM-07-2020-0026.',
    '[19] V. Zakamulin, "Not all bull and bear markets are alike: insights from a five-state hidden semi-Markov model," Risk Management, vol. 25, no. 1, art. 5, 2023, doi: 10.1057/s41283-022-00112-y.',
    '[20] E. Blanchard and P.-O. Goffard, "Data driven investment strategies using Bayesian inference in regime-switching models," Applied Stochastic Models in Business and Industry, vol. 41, no. 6, art. e70058, 2025, doi: 10.1002/asmb.70058.',
    '[21] A. Koukorinis, G. W. Peters, and G. Germano, "Generative-discriminative machine learning models for high-frequency financial regime classification," Methodology and Computing in Applied Probability, vol. 27, no. 2, art. 36, 2025, doi: 10.1007/s11009-025-10148-8.',
]


def poner_texto(parrafo, texto):
    if parrafo.runs:
        parrafo.runs[0].text = texto
        for run in parrafo.runs[1:]:
            run.text = ""
    else:
        parrafo.add_run(texto)


def insertar_despues(parrafo, texto=""):
    nuevo = OxmlElement("w:p")
    parrafo._p.addnext(nuevo)
    creado = Paragraph(nuevo, parrafo._parent)
    if texto:
        creado.add_run(texto)
        creado.paragraph_format.space_after = Pt(8)
    return creado


def buscar(documento, inicio):
    for parrafo in documento.paragraphs:
        if parrafo.text.strip().startswith(inicio):
            return parrafo
    raise KeyError(inicio)


def reemplazar_imagenes(documento):
    rutas = [
        CARPETA / "figuras" / "precio_regimenes.png",
        CARPETA / "figuras" / "retornos_observados.png",
        CARPETA / "figuras" / "comparacion_escenarios.png",
    ]
    if len(documento.inline_shapes) < 3:
        raise RuntimeError("El informe no tiene las tres figuras originales.")
    for forma, ruta in zip(documento.inline_shapes, rutas):
        rid = forma._inline.graphic.graphicData.pic.blipFill.blip.embed
        documento.part.related_parts[rid]._blob = ruta.read_bytes()


def actualizar_tabla_e2(documento):
    tabla = documento.tables[5]
    filas = {
        5: ["-2.46%", "18.69%", "-36.92%", "54.51%", "[-5.05%, 0.13%]"],
        6: ["-16.21%", "8.66%", "-37.53%", "-1.39%", "[-17.41%, -15.01%]"],
        7: ["10.06", "2.86", "3.00", "19.00", "[9.67, 10.46]"],
        8: ["65.54%", "12.30%", "34.00%", "92.00%", "[63.84%, 67.24%]"],
    }
    for indice, valores in filas.items():
        for columna, valor in enumerate(valores, start=2):
            tabla.rows[indice].cells[columna].text = valor


def actualizar_tabla_literatura(documento):
    for fila in documento.tables[0].rows:
        if "Bulla" in fila.cells[0].text:
            fila.cells[0].text = "Liu et al. (2024) [12]"
            fila.cells[1].text = "Markov jerárquico y retornos multivariados"
            fila.cells[2].text = "Identifica bull y bear en una sección amplia de activos"
            fila.cells[3].text = "Estima parámetros; no publica un experimento didáctico reproducible"


def main():
    documento = Document(INFORME)
    reemplazar_imagenes(documento)
    actualizar_tabla_e2(documento)
    actualizar_tabla_literatura(documento)

    poner_texto(
        buscar(documento, "Esta estructura"),
        "Esta estructura —un proceso de estado oculto que gobierna una secuencia observable— "
        "coincide con la definición del Modelo Oculto de Markov (HMM), propuesto por Baum y Petrie [3] "
        "y sistematizado por Rabiner [4]. Entre 2021 y 2026, modelos de Markov y HMM se han usado para "
        "regímenes bursátiles, volatilidad y asignación de portafolio [12]–[21]. Buena parte de esas "
        "aplicaciones calibra las matrices con un histórico y no publica semillas, réplicas ni intervalos "
        "de confianza. Este trabajo ocupa ese lugar: el experimento se puede volver a correr.",
    )
    poner_texto(
        buscar(documento, "En años recientes"),
        "Los clásicos siguen siendo el punto de partida. Hamilton [1] introdujo el cambio de régimen "
        "para los ciclos económicos. Baum y Petrie [3] y Rabiner [4] fijaron el HMM y el algoritmo Forward. "
        "Viterbi [8] aporta la decodificación. Nguyen [5] llevó un HMM al trading de acciones, y Dias, "
        "Vermunt y Ramos [7] compararon clases latentes y HMM en índices europeos. En la década reciente, "
        "Wang et al. [13] modelan precio y ambigüedad con cambio de régimen; Naik y Mohan [14] estiman "
        "volatilidad en la bolsa india; Mahmoudi y Ghaneei [15] y Raifu y Oshota [18] relacionan el petróleo "
        "con el mercado accionario; Chavoshi, Mansouri y Sheidani [16] ajustan un HMM para predicción; "
        "Athari, Kirikkaleli y Adebayo [17] estudian la bolsa alemana; Zakamulin [19] distingue cinco estados "
        "con un semi-Markov oculto; Liu, Maheu y Song [12] identifican mercados alcistas y bajistas con "
        "retornos de muchos activos; Blanchard y Goffard [20] ajustan un HMM gaussiano por inferencia "
        "bayesiana; y Koukorinis, Peters y Germano [21] clasifican regímenes de alta frecuencia con un HMM "
        "y máquinas de kernel. El vacío es de método, no de tema: faltan implementaciones didácticas con "
        "semilla fija, tres escenarios y estadísticos de 200 réplicas.",
    )
    poner_texto(
        buscar(documento, "El estudio se organizó"),
        "El estudio se organizó en siete fases: (F1) planteamiento del problema, (F2) revisión de literatura, "
        "(F3) diseño formal del modelo, (F4) implementación en Python, (F5) ejecución de escenarios con semillas "
        "fijas, (F6) análisis estadístico y (F7) comunicación. Las cifras de este documento se obtuvieron con "
        "Python 3.12.14, NumPy 2.5.4, pandas 3.1.1 y Matplotlib 3.11.2. No se usó hmmlearn: la simulación, "
        "el algoritmo Forward y Viterbi están escritos en hmm_mercado_financiero.py. Las figuras se exportaron a 300 dpi.",
    )
    poner_texto(
        buscar(documento, "Se definieron tres escenarios"),
        "Se definieron tres escenarios paramétricos. E1 usa las matrices del enunciado y T = 50. E2 mantiene "
        "T = 50 y eleva cada diagonal de A a 0.80; el 0.20 restante conserva la proporción de las salidas "
        "originales, de modo que la matriz queda [[0.80, 0.15, 0.05], [0.10, 0.80, 0.10], [0.05, 0.15, 0.80]]. "
        "E3 vuelve a las matrices del enunciado y duplica el horizonte, T = 100. En cada escenario se ejecutaron "
        "N = 200 réplicas con las semillas 1 a 200. Los intervalos de confianza al 95% se calcularon como "
        "media ± 1.96 · s/√n, con la desviación estándar muestral.",
    )
    poner_texto(
        buscar(documento, "Lectura de la tabla"),
        "En la línea base el retorno medio es −2.97% y su intervalo de confianza al 95% es [−4.87%, −1.07%]. "
        "Ese intervalo no incluye el cero: la media de las 200 réplicas es levemente negativa. La desviación "
        "estándar es 13.71% y las corridas van de −30.86% a 38.52%, así que una simulación suelta no distingue "
        "una ganancia de una pérdida. Al elevar la persistencia, los cambios de régimen bajan de 23.16 a 10.06 "
        "y la desviación del retorno sube de 13.71% a 18.69%. El intervalo de E2, [−5.05%, 0.13%], sí incluye "
        "el cero. Con 100 períodos el retorno medio es −6.08% y el intervalo [−8.51%, −3.64%] sigue por debajo "
        "de cero. La dispersión absoluta del retorno acumulado no baja, porque los choques se suman durante más "
        "días. Lo que se estima con más precisión es el acierto de Viterbi: su desviación pasa de 8.50 puntos "
        "porcentuales en E1 a 5.77 en E3.",
    )
    poner_texto(
        buscar(documento, "Los resultados muestran"),
        "Los resultados muestran que un HMM de tres regímenes produce trayectorias con rachas, drawdowns y "
        "tramos laterales, la estructura que Hamilton [1] y los trabajos recientes [12]–[21] documentan en "
        "precios reales. La validación de 4000 períodos confirma el generador: la mayor diferencia absoluta "
        "entre la transición empírica y A fue 0.027, y entre la emisión empírica y B fue 0.008. La frecuencia "
        "del régimen lateral fue 31.95%, que a un decimal es 31.9%, frente al 33.3% estacionario.",
    )
    poner_texto(
        buscar(documento, "La estadística Monte Carlo"),
        "La estadística de 200 réplicas deja tres lecturas. La media del retorno en la línea base es negativa "
        "y su intervalo no incluye el cero, pero la dispersión entre corridas es demasiado grande para decidir "
        "con una sola trayectoria. Subir la persistencia reduce los cambios de régimen y eleva la desviación "
        "del retorno, porque las rachas duran más. Alargar el horizonte a 100 períodos no estrecha el intervalo "
        "del retorno acumulado; estrecha la estimación del acierto de Viterbi. El algoritmo Forward, que calcula "
        "log P(O|λ), promedió −53.65 en E1, −52.76 en E2 y −107.24 en E3. El último valor es casi el doble "
        "porque la serie duplica su longitud: por período, las tres medias quedan alrededor de −1.07.",
    )

    algoritmo = buscar(documento, "Para cada escenario, el procedimiento")
    pseudocodigo = insertar_despues(
        algoritmo,
        "Pseudocódigo. precio ← 100; estado ← Categórica(π). Para t = 1, …, T: observación[t] ← "
        "Categórica(B[estado]); retorno[t] ← Uniforme(intervalo del par estado, observación); "
        "precio[t] ← precio[t−1] · (1 + retorno[t]); si t < T, estado ← Categórica(A[estado]). "
        "Al cerrar la serie: ruta ← Viterbi(observación) y log P(O|λ) ← Forward(observación). "
        "El experimento repite ese bloque con las semillas 1 a 200 en E1, E2 y E3.",
    )
    figura = insertar_despues(pseudocodigo)
    figura.alignment = WD_ALIGN_PARAGRAPH.CENTER
    figura.add_run().add_picture(str(CARPETA / "figuras" / "diagrama_flujo.png"), width=Inches(5.4))
    pie = insertar_despues(
        figura,
        "Figura 4. Flujo de una réplica: simulación del HMM, decodificación, evaluación y métricas.",
    )
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in pie.runs:
        run.italic = True
        run.font.size = Pt(11)

    cierre_fig3 = buscar(documento, "Figura 3.")
    bloque = insertar_despues(cierre_fig3)
    bloque.alignment = WD_ALIGN_PARAGRAPH.CENTER
    bloque.add_run().add_picture(
        str(CARPETA / "figuras" / "comparacion_monte_carlo.png"), width=Inches(6.2)
    )
    pie_mc = insertar_despues(
        bloque,
        "Figura 5. Media e intervalo de confianza al 95% de cuatro métricas en los tres escenarios. "
        "Cada barra resume 200 réplicas con semillas 1 a 200.",
    )
    pie_mc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in pie_mc.runs:
        run.italic = True
        run.font.size = Pt(11)

    nota = buscar(documento, "Nota: Las referencias")
    poner_texto(
        nota,
        "Las referencias [1]–[11] reúnen los clásicos de Markov y HMM y antecedentes anteriores a 2021. "
        "Las referencias [12]–[21] son artículos de 2021 a 2026. La entrada que antes ocupaba el número [12] "
        "se reemplazó: el artículo 118984 de Expert Systems with Applications no corresponde a un modelo de mercados.",
    )
    ancla = buscar(documento, "[12]")
    poner_texto(ancla, REFERENCIAS_NUEVAS[0])
    previo = ancla
    for texto in REFERENCIAS_NUEVAS[1:]:
        previo = insertar_despues(previo, texto)

    anexo = buscar(documento, "Para reproducir los resultados")
    poner_texto(
        anexo,
        "Para reproducir los resultados: clonar el repositorio, instalar requirements.txt y ejecutar "
        "python hmm_mercado_financiero.py con Python 3.12.14 y NumPy 2.5.4. El escenario ilustrado usa "
        "SEMILLA_PRINCIPAL = 42. Las 600 réplicas quedan en datos/replicas_monte_carlo.csv y en "
        "datos/replicas_monte_carlo.xlsx. El resumen estadístico está en datos/resumen_monte_carlo.json "
        "y las versiones, en datos/entorno.txt.",
    )

    resumen = buscar(documento, "Los mercados financieros alternan")
    palabras = len(resumen.text.split())
    documento.save(INFORME)
    print(f"Resumen: {palabras} palabras")
    print(f"Guardado: {INFORME}")


if __name__ == "__main__":
    main()
