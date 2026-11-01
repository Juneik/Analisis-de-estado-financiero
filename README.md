# Análisis de estado financiero

Simulación de un modelo oculto de Markov con tres regímenes de mercado: alcista, lateral y bajista. El código genera 50 períodos de trading, un precio a partir de los retornos y las métricas pedidas en la actividad.

Autor: Paul Ramirez. Asignatura: Simulación, Semestre V, IU Digital.

## Qué hay en el repositorio

- `hmm_mercado_financiero.py` — algoritmo. También corre en Google Colab.
- `hmm_mercado_financiero.ipynb` — el mismo algoritmo en un cuaderno.
- `Ramirez_Paul_Markov.docx` — informe con introducción, metodología, resultados y conclusiones.
- `Ramirez_Paul_Markov_datos.xlsx` — parámetros, serie del escenario principal, métricas y cinco semillas.
- `datos/escenario_principal.csv` — la misma serie en CSV.
- `figuras/` — precio por régimen, retornos observados y comparación de escenarios.

El escenario que desarrolla el informe usa la semilla 42. Para otro mercado, cambia `SEMILLA_PRINCIPAL` al inicio de `hmm_mercado_financiero.py` y vuelve a ejecutarlo.

## Cómo ejecutarlo

En local, con las dependencias de `requirements.txt`:

```bash
python hmm_mercado_financiero.py
```

Para regenerar el informe, el Excel y el cuaderno:

```bash
python generar_informe.py
```

En Google Colab abre `hmm_mercado_financiero.ipynb` y ejecuta el cuaderno completo.

La simulación es un ejercicio de distribuciones de probabilidad. No es asesoría de inversión.
