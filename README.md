# Análisis de estado financiero

Simulación de un modelo oculto de Markov con tres regímenes de mercado: alcista, lateral y bajista. El experimento corre tres escenarios, con 200 réplicas y semillas fijas, y resume cada métrica con media, desviación estándar, mínimo, máximo e intervalo de confianza al 95%.

Autores: Camilo Pieschacón Vargas, María Fernanda Buitrago Rodríguez y Paul Isaac Tirado Ramírez. Asignatura: Simulación, Semestre V, IU Digital. Profesor: Julián Andrés Loaiza.

## Informe

`Pieschacon_Camilo_Tirado_Paul_Buitrago_MariaFernanda.docx`

## Cómo ejecutarlo

El entorno con el que se calcularon las cifras del informe es Python 3.12.14, NumPy 2.5.4, pandas 3.1.1 y Matplotlib 3.11.2. Esas versiones quedan escritas en `datos/entorno.txt` al correr el programa. No se usa hmmlearn: la simulación, Forward y Viterbi están en el propio código.

```bash
python hmm_mercado_financiero.py
```

En Google Colab abre `hmm_mercado_financiero.ipynb` y ejecuta el cuaderno. Para otro mercado ilustrativo, cambia `SEMILLA_PRINCIPAL`. Las 200 réplicas usan siempre las semillas 1 a 200.

## Escenarios

- E1, línea base: matrices del enunciado y 50 períodos.
- E2, alta persistencia: cada diagonal de A pasa a 0.80 y el resto conserva la proporción de las salidas. La matriz queda `[[0.80, 0.15, 0.05], [0.10, 0.80, 0.10], [0.05, 0.15, 0.80]]`.
- E3, horizonte extendido: matrices de E1 y 100 períodos.

## Archivos

- `hmm_mercado_financiero.py` — algoritmo.
- `hmm_mercado_financiero.ipynb` — el mismo algoritmo para Colab.
- `datos/escenario_principal.csv` — serie de la semilla 42.
- `datos/replicas_monte_carlo.csv` y `datos/replicas_monte_carlo.xlsx` — las 600 réplicas.
- `datos/resumen_monte_carlo.json` — media, desviación, mínimo, máximo e intervalo de confianza.
- `figuras/` — precio, retornos, cinco semillas, diagrama de flujo y comparación de escenarios, a 300 dpi.

La simulación es un ejercicio de distribuciones de probabilidad. No es asesoría de inversión.
