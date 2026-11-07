"""
Modelo oculto de Markov para regímenes de mercado financiero.

Simula 50 períodos de trading, construye un precio a partir de los retornos
observados y calcula métricas, cambios de régimen, recomendación y riesgo.

Pensado para ejecutarse en Google Colab o en local:
    python hmm_mercado_financiero.py

Cambia SEMILLA_PRINCIPAL para obtener otro escenario.
"""

import json
import platform
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Parámetros del modelo (los define el enunciado)
# ----------------------------------------------------------------------

ESTADOS = ["Mercado Alcista", "Mercado Lateral", "Mercado Bajista"]
OBSERVACIONES = ["Retorno Positivo", "Retorno Neutral", "Retorno Negativo"]

# A[i, j] = P(estado_{t+1} = j | estado_t = i)
A = np.array([
    [0.6, 0.3, 0.1],  # Alcista
    [0.3, 0.4, 0.3],  # Lateral
    [0.1, 0.3, 0.6],  # Bajista
])

# B[i, k] = P(observación_t = k | estado_t = i)
B = np.array([
    [0.7, 0.2, 0.1],  # Alcista
    [0.3, 0.4, 0.3],  # Lateral
    [0.1, 0.2, 0.7],  # Bajista
])

PI = np.array([0.4, 0.3, 0.3])

PRECIO_INICIAL = 100.0
N_PERIODOS = 50
N_PERIODOS_EXTENDIDO = 100
N_REPLICAS = 200
SEMILLA_PRINCIPAL = 42
SEMILLAS_COMPARACION = [7, 21, 42, 99, 2026]
N_VALIDACION = 4000
DPI = 300

# Alta persistencia: la diagonal pasa a 0.80 y el 0.20 restante conserva
# la proporción de las salidas de la matriz original.
A_ALTA_PERSISTENCIA = np.array([
    [0.80, 0.15, 0.05],
    [0.10, 0.80, 0.10],
    [0.05, 0.15, 0.80],
])

COLORES_REGIMEN = ["#1e8f4e", "#e6b325", "#d64545"]
COLORES_OBS = ["#1e8f4e", "#7f8c8d", "#d64545"]
ETIQUETAS_CORTAS = ["Alcista", "Lateral", "Bajista"]

# Magnitud del retorno diario, condicional al estado y a la observación.
# Cada par se sortea con una distribución uniforme en el intervalo.
# El signo queda alineado con la etiqueta observada.
RANGOS_RETORNO = {
    (0, 0): (0.006, 0.028),
    (0, 1): (-0.002, 0.004),
    (0, 2): (-0.015, -0.003),
    (1, 0): (0.003, 0.012),
    (1, 1): (-0.004, 0.004),
    (1, 2): (-0.012, -0.003),
    (2, 0): (0.003, 0.010),
    (2, 1): (-0.005, 0.002),
    (2, 2): (-0.032, -0.006),
}


class HMMMercado:
    """HMM de tres regímenes. Simula la cadena y decodifica con Viterbi."""

    def __init__(self, estados, observaciones, matriz_a, matriz_b, pi):
        self.estados = list(estados)
        self.observaciones = list(observaciones)
        self.A = np.array(matriz_a, dtype=float)
        self.B = np.array(matriz_b, dtype=float)
        self.pi = np.array(pi, dtype=float)
        self._validar()

    def _validar(self):
        if self.A.shape != (len(self.estados), len(self.estados)):
            raise ValueError("La matriz A no coincide con el número de estados.")
        if self.B.shape != (len(self.estados), len(self.observaciones)):
            raise ValueError("La matriz B no coincide con estados y observaciones.")
        if self.pi.shape != (len(self.estados),):
            raise ValueError("La distribución inicial no coincide con los estados.")
        for nombre, matriz in (("A", self.A), ("B", self.B)):
            if np.any(matriz < 0):
                raise ValueError(f"La matriz {nombre} tiene probabilidades negativas.")
            sumas = matriz.sum(axis=1)
            if not np.allclose(sumas, 1.0):
                raise ValueError(f"Las filas de {nombre} deben sumar 1. Sumas: {sumas}")
        if np.any(self.pi < 0) or not np.isclose(self.pi.sum(), 1.0):
            raise ValueError("La distribución inicial debe ser no negativa y sumar 1.")

    def simular(self, n_periodos, rng):
        """Genera estados, observaciones, retornos y la trayectoria del precio."""
        n_estados = len(self.estados)
        n_obs = len(self.observaciones)
        estados = np.empty(n_periodos, dtype=int)
        obs = np.empty(n_periodos, dtype=int)
        retornos = np.empty(n_periodos, dtype=float)

        estados[0] = rng.choice(n_estados, p=self.pi)
        obs[0] = rng.choice(n_obs, p=self.B[estados[0]])
        retornos[0] = self._magnitud(estados[0], obs[0], rng)

        for t in range(1, n_periodos):
            estados[t] = rng.choice(n_estados, p=self.A[estados[t - 1]])
            obs[t] = rng.choice(n_obs, p=self.B[estados[t]])
            retornos[t] = self._magnitud(estados[t], obs[t], rng)

        precios = np.empty(n_periodos + 1, dtype=float)
        precios[0] = PRECIO_INICIAL
        for t in range(n_periodos):
            precios[t + 1] = precios[t] * (1.0 + retornos[t])

        return estados, obs, retornos, precios

    def _magnitud(self, estado, observacion, rng):
        bajo, alto = RANGOS_RETORNO[(int(estado), int(observacion))]
        return float(rng.uniform(bajo, alto))

    def viterbi(self, obs):
        """Secuencia de estados más probable dada solo la serie de observaciones."""
        n = len(self.estados)
        tiempo = len(obs)
        log_a = np.log(self.A)
        log_b = np.log(self.B)
        log_pi = np.log(self.pi)

        delta = np.empty((tiempo, n))
        psi = np.zeros((tiempo, n), dtype=int)
        delta[0] = log_pi + log_b[:, obs[0]]

        for t in range(1, tiempo):
            for j in range(n):
                puntajes = delta[t - 1] + log_a[:, j]
                psi[t, j] = int(np.argmax(puntajes))
                delta[t, j] = puntajes[psi[t, j]] + log_b[j, obs[t]]

        camino = np.empty(tiempo, dtype=int)
        camino[-1] = int(np.argmax(delta[-1]))
        for t in range(tiempo - 2, -1, -1):
            camino[t] = psi[t + 1, camino[t + 1]]
        return camino

    def log_verosimilitud(self, obs):
        """Log P(O|λ) con el algoritmo Forward en escala logarítmica."""
        n = len(self.estados)
        log_a = np.log(self.A)
        log_b = np.log(self.B)
        alpha = np.log(self.pi) + log_b[:, obs[0]]
        for t in range(1, len(obs)):
            nuevo = np.empty(n)
            for j in range(n):
                nuevo[j] = np.logaddexp.reduce(alpha + log_a[:, j]) + log_b[j, obs[t]]
            alpha = nuevo
        return float(np.logaddexp.reduce(alpha))

    def distribucion_estacionaria(self):
        """Resuelve π = π A con la restricción de que las probabilidades sumen 1."""
        n = len(self.estados)
        sistema = (self.A - np.eye(n)).T
        sistema[-1, :] = 1.0
        lado_derecho = np.zeros(n)
        lado_derecho[-1] = 1.0
        return np.linalg.solve(sistema, lado_derecho)

    def duracion_esperada(self):
        """E[duración de i] = 1 / (1 - A_ii), por la distribución geométrica."""
        return 1.0 / (1.0 - np.diag(self.A))


def rachas(estados):
    """Agrupa períodos consecutivos del mismo régimen: (estado, longitud, inicio)."""
    grupos = []
    actual = int(estados[0])
    longitud = 1
    inicio = 0
    for t in range(1, len(estados)):
        if int(estados[t]) == actual:
            longitud += 1
        else:
            grupos.append((actual, longitud, inicio))
            actual = int(estados[t])
            longitud = 1
            inicio = t
    grupos.append((actual, longitud, inicio))
    return grupos


def duracion_promedio(estados):
    acumulado = {i: [] for i in range(len(ESTADOS))}
    for estado, longitud, _ in rachas(estados):
        acumulado[estado].append(longitud)
    promedio = {}
    for i, lista in acumulado.items():
        promedio[i] = float(np.mean(lista)) if lista else None
    return promedio, acumulado


def drawdown_maximo(precios):
    maximo_previo = np.maximum.accumulate(precios)
    caidas = precios / maximo_previo - 1.0
    indice = int(np.argmin(caidas))
    return float(caidas[indice]), indice


def cambios_de_regimen(estados):
    cambios = []
    for t in range(1, len(estados)):
        if int(estados[t]) != int(estados[t - 1]):
            cambios.append({
                "periodo": t + 1,
                "desde": ESTADOS[int(estados[t - 1])],
                "hacia": ESTADOS[int(estados[t])],
            })
    return cambios


def volatilidad_por_regimen(estados, retornos):
    resultado = {}
    for i in range(len(ESTADOS)):
        muestra = retornos[estados == i]
        if len(muestra) >= 2:
            resultado[i] = float(np.std(muestra, ddof=1))
        else:
            resultado[i] = None
    return resultado


def metricas_escenario(estados, obs, retornos, precios):
    promedio, detalle = duracion_promedio(estados)
    dd, idx_dd = drawdown_maximo(precios)
    conteo = np.bincount(estados, minlength=len(ESTADOS))
    return {
        "retorno_total": float(precios[-1] / precios[0] - 1.0),
        "precio_final": float(precios[-1]),
        "drawdown_maximo": dd,
        "periodo_drawdown": idx_dd,
        "duracion_promedio": promedio,
        "rachas": detalle,
        "volatilidad": volatilidad_por_regimen(estados, retornos),
        "dias_por_regimen": conteo.tolist(),
        "n_cambios": len(cambios_de_regimen(estados)),
        "peor_retorno": float(retornos.min()),
        "mejor_retorno": float(retornos.max()),
        "retorno_medio": float(retornos.mean()),
        "observaciones": np.bincount(obs, minlength=len(OBSERVACIONES)).tolist(),
    }


def recomendacion(estado_actual, metricas):
    persistencia = float(A[estado_actual, estado_actual])
    textos = {
        0: (
            "El último período cayó en mercado alcista. La matriz de transición "
            f"le asigna {persistencia:.0%} de probabilidad de continuar alcista en "
            "el período siguiente, así que el sesgo del modelo favorece mantener "
            "exposición compradora. Conviene acompañar la posición con un límite "
            "de pérdida: desde alcista todavía hay 10% de probabilidad de saltar "
            "directo a bajista y 30% de pasar a lateral."
        ),
        1: (
            "El último período cayó en mercado lateral. La persistencia de este "
            f"régimen es {persistencia:.0%} y las salidas hacia alcista o bajista "
            "están equilibradas (30% cada una). El modelo no justifica perseguir "
            "una tendencia: el tamaño de la posición debería ser menor y la "
            "decisión, esperar una secuencia de retornos que incline el régimen."
        ),
        2: (
            "El último período cayó en mercado bajista. La persistencia es "
            f"{persistencia:.0%}, la más alta junto con la del régimen alcista, "
            "así que lo más probable es que la presión negativa continúe. La "
            "postura coherente con el modelo es reducir exposición, evitar "
            "promediar a la baja y esperar un retorno positivo sostenido antes "
            "de reabrir riesgo. La probabilidad de un rebote directo a alcista "
            "es solo 10%."
        ),
    }
    riesgo = (
        f"En este escenario el drawdown máximo fue {metricas['drawdown_maximo']:.1%} "
        f"y el peor retorno diario fue {metricas['peor_retorno']:.1%}. "
        f"Hubo {metricas['n_cambios']} cambios de régimen en {N_PERIODOS} períodos: "
        "cada cambio es un punto en el que una regla de trading puede llegar tarde."
    )
    return textos[estado_actual], riesgo


def _cerrar(fig):
    if matplotlib.get_backend().lower() != "agg":
        plt.show()
    plt.close(fig)


def graficar_precio(estados, precios, ruta):
    periodos = np.arange(1, len(estados) + 1)
    fig, ax = plt.subplots(figsize=(12, 5.2))
    for t, estado in enumerate(estados):
        ax.axvspan(t + 0.5, t + 1.5, color=COLORES_REGIMEN[int(estado)], alpha=0.28, lw=0)
    ax.plot(periodos, precios[1:], color="#1c1c1c", lw=2.1, label="Precio simulado")
    ax.axhline(PRECIO_INICIAL, color="#888888", ls="--", lw=0.8)
    ax.set_xlim(0.5, len(estados) + 0.5)
    ax.set_xlabel("Período de trading")
    ax.set_ylabel("Precio (base 100)")
    ax.set_title("Precio simulado según el régimen de mercado")
    marcas = [
        plt.matplotlib.patches.Patch(color=color, alpha=0.45, label=nombre)
        for color, nombre in zip(COLORES_REGIMEN, ESTADOS)
    ]
    marcas.append(plt.Line2D([0], [0], color="#1c1c1c", lw=2.1, label="Precio"))
    ax.legend(
        handles=marcas, loc="upper center", bbox_to_anchor=(0.5, -0.18),
        ncol=4, frameon=False,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight")
    _cerrar(fig)


def graficar_retornos(obs, retornos, ruta):
    periodos = np.arange(1, len(retornos) + 1)
    colores = [COLORES_OBS[int(k)] for k in obs]
    fig, ax = plt.subplots(figsize=(12, 4.6))
    ax.bar(periodos, retornos * 100, color=colores, width=0.8)
    ax.axhline(0, color="#1c1c1c", lw=0.8)
    ax.set_xlim(0.5, len(retornos) + 0.5)
    ax.set_xlabel("Período de trading")
    ax.set_ylabel("Retorno (%)")
    ax.set_title("Retornos observados")
    marcas = [
        plt.matplotlib.patches.Patch(color=color, label=nombre)
        for color, nombre in zip(COLORES_OBS, OBSERVACIONES)
    ]
    ax.legend(
        handles=marcas, loc="upper center", bbox_to_anchor=(0.5, -0.18),
        ncol=3, frameon=False,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight")
    _cerrar(fig)


def graficar_comparacion(filas, ruta):
    nombres = [f"Semilla {fila['semilla']}" for fila in filas]
    valores = [fila["retorno_total"] * 100 for fila in filas]
    colores = ["#1e8f4e" if v >= 0 else "#d64545" for v in valores]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.bar(nombres, valores, color=colores)
    ax.axhline(0, color="#1c1c1c", lw=0.8)
    ax.set_ylabel("Retorno acumulado (%)")
    ax.set_title("Cinco simulaciones con la misma especificación")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight")
    _cerrar(fig)


def tabla_emision_empirica(estados, obs):
    conteo = np.zeros_like(B)
    for estado, observacion in zip(estados, obs):
        conteo[int(estado), int(observacion)] += 1
    totales = conteo.sum(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        frecuencias = np.divide(conteo, totales, out=np.zeros_like(conteo), where=totales > 0)
    return frecuencias, conteo


def correr_escenario(modelo, n_periodos, semilla):
    rng = np.random.default_rng(semilla)
    estados, obs, retornos, precios = modelo.simular(n_periodos, rng)
    decodificado = modelo.viterbi(obs)
    datos = metricas_escenario(estados, obs, retornos, precios)
    datos.update({
        "semilla": semilla,
        "estados": estados,
        "obs": obs,
        "retornos": retornos,
        "precios": precios,
        "viterbi": decodificado,
        "acierto_viterbi": float(np.mean(decodificado == estados)),
        "cambios": cambios_de_regimen(estados),
        "estado_final": int(estados[-1]),
    })
    return datos


def validar_frecuencias(modelo):
    rng = np.random.default_rng(1)
    estados, obs, _, _ = modelo.simular(N_VALIDACION, rng)
    frec_estados = np.bincount(estados, minlength=3) / N_VALIDACION
    emision, _ = tabla_emision_empirica(estados, obs)
    transiciones = np.zeros_like(A)
    for t in range(1, len(estados)):
        transiciones[estados[t - 1], estados[t]] += 1
    totales = transiciones.sum(axis=1, keepdims=True)
    frec_trans = transiciones / totales
    return {
        "n": N_VALIDACION,
        "frec_estados": frec_estados,
        "emision": emision,
        "transicion": frec_trans,
    }


def imprimir_escenario(datos):
    print("=" * 72)
    print(f"ESCENARIO PRINCIPAL  |  semilla {datos['semilla']}  |  {N_PERIODOS} períodos")
    print("=" * 72)
    print(f"Precio inicial: {datos['precios'][0]:.2f}")
    print(f"Precio final:   {datos['precio_final']:.2f}")
    print(f"Retorno acumulado: {datos['retorno_total']:.2%}")
    print(f"Drawdown máximo:   {datos['drawdown_maximo']:.2%}")
    print(f"Cambios de régimen: {datos['n_cambios']}")
    print(f"Acierto de Viterbi frente al estado simulado: {datos['acierto_viterbi']:.1%}")
    print()
    print("Duración promedio observada (períodos) y volatilidad diaria:")
    for i, nombre in enumerate(ESTADOS):
        dur = datos["duracion_promedio"][i]
        vol = datos["volatilidad"][i]
        dur_txt = "sin visitas" if dur is None else f"{dur:.2f}"
        vol_txt = "n < 2" if vol is None else f"{vol:.2%}"
        print(f"  {nombre}: días {datos['dias_por_regimen'][i]:2d} | duración {dur_txt} | vol {vol_txt}")
    print()
    print("Cambios de régimen:")
    for cambio in datos["cambios"]:
        print(f"  Período {cambio['periodo']:2d}: {cambio['desde']} -> {cambio['hacia']}")
    texto, riesgo = recomendacion(datos["estado_final"], datos)
    print()
    print("Recomendación según el régimen del último período:")
    print(texto)
    print()
    print("Lectura de riesgo:")
    print(riesgo)


def resumir_muestra(valores):
    """Media, desviación estándar muestral, mínimo, máximo e IC del 95%."""
    muestra = np.asarray(valores, dtype=float)
    media = float(muestra.mean())
    desv = float(muestra.std(ddof=1))
    margen = 1.96 * desv / np.sqrt(len(muestra))
    return {
        "media": media,
        "desv": desv,
        "minimo": float(muestra.min()),
        "maximo": float(muestra.max()),
        "ic_bajo": media - margen,
        "ic_alto": media + margen,
        "n": int(len(muestra)),
    }


def definicion_escenarios():
    return [
        {
            "codigo": "E1",
            "nombre": "Línea base",
            "descripcion": "Parámetros del enunciado",
            "periodos": N_PERIODOS,
            "transicion": A,
        },
        {
            "codigo": "E2",
            "nombre": "Alta persistencia",
            "descripcion": "Diagonales de A en 0.80; las salidas conservan su proporción",
            "periodos": N_PERIODOS,
            "transicion": A_ALTA_PERSISTENCIA,
        },
        {
            "codigo": "E3",
            "nombre": "Horizonte extendido",
            "descripcion": "Parámetros base con el doble de períodos",
            "periodos": N_PERIODOS_EXTENDIDO,
            "transicion": A,
        },
    ]


def monte_carlo(n_replicas=N_REPLICAS):
    """Corre las semillas 1..n en cada escenario y resume las métricas."""
    metricas = (
        "retorno_total",
        "drawdown_maximo",
        "n_cambios",
        "acierto_viterbi",
        "log_verosimilitud",
    )
    replicas = []
    resumen = []
    for escenario in definicion_escenarios():
        modelo = HMMMercado(
            ESTADOS, OBSERVACIONES, escenario["transicion"], B, PI
        )
        columnas = {nombre: [] for nombre in metricas}
        for semilla in range(1, n_replicas + 1):
            datos = correr_escenario(modelo, escenario["periodos"], semilla)
            log_p = modelo.log_verosimilitud(datos["obs"])
            fila = {
                "escenario": escenario["codigo"],
                "nombre": escenario["nombre"],
                "semilla": semilla,
                "periodos": escenario["periodos"],
                "retorno_total": datos["retorno_total"],
                "drawdown_maximo": datos["drawdown_maximo"],
                "n_cambios": datos["n_cambios"],
                "acierto_viterbi": datos["acierto_viterbi"],
                "log_verosimilitud": log_p,
                "precio_final": datos["precio_final"],
            }
            replicas.append(fila)
            for nombre in metricas:
                columnas[nombre].append(fila[nombre])
        resumen.append({
            "codigo": escenario["codigo"],
            "nombre": escenario["nombre"],
            "descripcion": escenario["descripcion"],
            "periodos": escenario["periodos"],
            "metricas": {nombre: resumir_muestra(columnas[nombre]) for nombre in metricas},
        })
    return replicas, resumen


def graficar_monte_carlo(resumen, ruta):
    paneles = [
        ("retorno_total", "Retorno acumulado medio", True),
        ("drawdown_maximo", "Drawdown máximo medio", True),
        ("n_cambios", "Cambios de régimen medios", False),
        ("acierto_viterbi", "Acierto medio de Viterbi", True),
    ]
    fig, ejes = plt.subplots(2, 2, figsize=(10.5, 7.2))
    nombres = [item["codigo"] for item in resumen]
    for ax, (clave, titulo, es_proporcion) in zip(ejes.ravel(), paneles):
        medias = [item["metricas"][clave]["media"] for item in resumen]
        bajos = [item["metricas"][clave]["ic_bajo"] for item in resumen]
        altos = [item["metricas"][clave]["ic_alto"] for item in resumen]
        if es_proporcion:
            medias = [100 * valor for valor in medias]
            bajos = [100 * valor for valor in bajos]
            altos = [100 * valor for valor in altos]
            ylabel = "Porcentaje"
        else:
            ylabel = "Cantidad de cambios"
        yerr = np.vstack([
            np.array(medias) - np.array(bajos),
            np.array(altos) - np.array(medias),
        ])
        ax.bar(nombres, medias, color=["#1F4E79", "#5B8FA8", "#C4A35A"], width=0.62)
        ax.errorbar(nombres, medias, yerr=yerr, fmt="none", ecolor="#1c1c1c", capsize=4, lw=1)
        ax.axhline(0, color="#888888", lw=0.6)
        ax.set_title(titulo)
        ax.set_ylabel(ylabel)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight")
    _cerrar(fig)


def diagrama_flujo(ruta):
    pasos = [
        "Fijar semilla, horizonte y parámetros π, A, B",
        "Sortear el régimen inicial con la categórica π",
        "Sortear la observación con la fila de B",
        "Sortear la magnitud con la uniforme del par (estado, observación)",
        "Actualizar el precio: P(t) = P(t-1) · (1 + r)",
        "Si quedan períodos, transitar con la fila de A y volver",
        "Decodificar con Viterbi y evaluar P(O|λ) con Forward",
        "Calcular métricas y repetir el escenario con otra semilla",
    ]
    fig, ax = plt.subplots(figsize=(8.2, 10.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(pasos) + 1)
    ax.axis("off")
    for indice, texto in enumerate(pasos):
        y = len(pasos) - indice
        caja = FancyBboxPatch(
            (0.7, y - 0.38), 8.6, 0.76,
            boxstyle="round,pad=0.08,rounding_size=0.08",
            facecolor="#E8F0F7" if indice not in (0, len(pasos) - 1) else "#1F4E79",
            edgecolor="#1F4E79",
            lw=1.1,
        )
        ax.add_patch(caja)
        ax.text(
            5, y, texto, ha="center", va="center", fontsize=9,
            color="white" if indice in (0, len(pasos) - 1) else "#1c1c1c",
        )
        if indice < len(pasos) - 1:
            ax.add_patch(FancyArrowPatch(
                (5, y - 0.42), (5, y - 0.62),
                arrowstyle="-|>", mutation_scale=12, color="#1F4E79", lw=1.1,
            ))
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight")
    _cerrar(fig)


def imprimir_monte_carlo(resumen):
    print()
    print("=" * 72)
    print(f"MONTE CARLO  |  {N_REPLICAS} réplicas  |  semillas 1 a {N_REPLICAS}")
    print("=" * 72)
    for escenario in resumen:
        print(f"\n{escenario['codigo']} — {escenario['nombre']} ({escenario['periodos']} períodos)")
        print(f"{'Métrica':<22} {'Media':>10} {'Desv.':>10} {'Mín':>10} {'Máx':>10} {'IC 95%':>22}")
        for nombre, etiqueta, como_pct in (
            ("retorno_total", "Retorno acumulado", True),
            ("drawdown_maximo", "Drawdown máximo", True),
            ("n_cambios", "Cambios de régimen", False),
            ("acierto_viterbi", "Acierto Viterbi", True),
            ("log_verosimilitud", "Log-verosimilitud", False),
        ):
            stats = escenario["metricas"][nombre]
            if como_pct:
                texto = (
                    f"{etiqueta:<22} {stats['media']:>10.2%} {stats['desv']:>10.2%} "
                    f"{stats['minimo']:>10.2%} {stats['maximo']:>10.2%} "
                    f"[{stats['ic_bajo']:.2%}, {stats['ic_alto']:.2%}]"
                )
            else:
                texto = (
                    f"{etiqueta:<22} {stats['media']:>10.2f} {stats['desv']:>10.2f} "
                    f"{stats['minimo']:>10.2f} {stats['maximo']:>10.2f} "
                    f"[{stats['ic_bajo']:.2f}, {stats['ic_alto']:.2f}]"
                )
            print(texto)


def guardar_monte_carlo(replicas, resumen, datos_dir):
    frame = pd.DataFrame(replicas)
    frame.to_csv(datos_dir / "replicas_monte_carlo.csv", index=False, encoding="utf-8-sig")
    with (datos_dir / "resumen_monte_carlo.json").open("w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, ensure_ascii=False, indent=2)
    try:
        frame.to_excel(datos_dir / "replicas_monte_carlo.xlsx", index=False)
    except ImportError:
        print("openpyxl no está instalado: el detalle quedó en CSV.")
    return frame


def guardar_entorno(ruta):
    lineas = [
        f"python {sys.version.split()[0]}",
        f"numpy {np.__version__}",
        f"pandas {pd.__version__}",
        f"matplotlib {matplotlib.__version__}",
        f"plataforma {platform.platform()}",
        "hmmlearn no se usa: el HMM, Forward y Viterbi están implementados en este archivo.",
    ]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print()
    print("Entorno:")
    print("\n".join(lineas))


def guardar_tabla(datos, ruta):
    frame = pd.DataFrame({
        "periodo": np.arange(1, N_PERIODOS + 1),
        "estado": [ESTADOS[i] for i in datos["estados"]],
        "estado_viterbi": [ESTADOS[i] for i in datos["viterbi"]],
        "observacion": [OBSERVACIONES[i] for i in datos["obs"]],
        "retorno": datos["retornos"],
        "precio_cierre": datos["precios"][1:],
    })
    frame.to_csv(ruta, index=False, encoding="utf-8-sig")
    return frame


def main():
    plt.rcParams["axes.unicode_minus"] = False
    carpeta = Path(__file__).resolve().parent
    figuras = carpeta / "figuras"
    datos_dir = carpeta / "datos"
    figuras.mkdir(exist_ok=True)
    datos_dir.mkdir(exist_ok=True)

    modelo = HMMMercado(ESTADOS, OBSERVACIONES, A, B, PI)
    estacionaria = modelo.distribucion_estacionaria()
    duracion_teo = modelo.duracion_esperada()

    print("Distribución estacionaria teórica:")
    for i, nombre in enumerate(ESTADOS):
        print(f"  {nombre}: {estacionaria[i]:.3f} | duración esperada {duracion_teo[i]:.2f} períodos")

    validacion = validar_frecuencias(modelo)
    print()
    print(f"Frecuencia de estados en {N_VALIDACION} períodos (semilla 1):")
    for i, nombre in enumerate(ESTADOS):
        print(f"  {nombre}: {validacion['frec_estados'][i]:.3f}")

    principal = correr_escenario(modelo, N_PERIODOS, SEMILLA_PRINCIPAL)
    principal["log_verosimilitud"] = modelo.log_verosimilitud(principal["obs"])
    imprimir_escenario(principal)
    print(f"Log-verosimilitud Forward: {principal['log_verosimilitud']:.2f}")
    graficar_precio(principal["estados"], principal["precios"], figuras / "precio_regimenes.png")
    graficar_retornos(principal["obs"], principal["retornos"], figuras / "retornos_observados.png")
    guardar_tabla(principal, datos_dir / "escenario_principal.csv")
    diagrama_flujo(figuras / "diagrama_flujo.png")

    comparacion = [correr_escenario(modelo, N_PERIODOS, semilla) for semilla in SEMILLAS_COMPARACION]
    print()
    print("Cinco escenarios (misma especificación, distinta semilla):")
    print(f"{'Semilla':>8} {'Retorno':>10} {'Drawdown':>10} {'Cambios':>8} {'Régimen final'}")
    for fila in comparacion:
        print(
            f"{fila['semilla']:8d} {fila['retorno_total']:10.2%} "
            f"{fila['drawdown_maximo']:10.2%} {fila['n_cambios']:8d}  {ESTADOS[fila['estado_final']]}"
        )
    graficar_comparacion(comparacion, figuras / "comparacion_escenarios.png")

    replicas, resumen = monte_carlo()
    imprimir_monte_carlo(resumen)
    guardar_monte_carlo(replicas, resumen, datos_dir)
    graficar_monte_carlo(resumen, figuras / "comparacion_monte_carlo.png")
    replica_42 = next(
        fila for fila in replicas
        if fila["escenario"] == "E1" and fila["semilla"] == SEMILLA_PRINCIPAL
    )
    if not np.isclose(replica_42["retorno_total"], principal["retorno_total"]):
        raise RuntimeError("La réplica E1 con semilla 42 no coincide con el escenario principal.")
    guardar_entorno(datos_dir / "entorno.txt")

    return {
        "modelo": modelo,
        "estacionaria": estacionaria,
        "duracion_teorica": duracion_teo,
        "validacion": validacion,
        "principal": principal,
        "comparacion": comparacion,
        "replicas": replicas,
        "resumen": resumen,
    }


if __name__ == "__main__":
    main()
