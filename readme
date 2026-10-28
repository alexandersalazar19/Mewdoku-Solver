# Meowdoku Solver

Script de python que resuelve automáticamente los niveles del juego **Meowdoku** para celular Android.


## Cómo funciona

1. Captura la pantalla del celular con `adb`.
2. Detecta el tamaño y la posición del tablero (`N×N`) con OpenCV.
3. Lee el color de cada celda y arma la matriz de regiones.
4. Detecta los gatos que el nivel ya trae puestos.
5. Resuelve el puzzle usando backtracking.
6. Toca las celdas de la solución con `adb shell input tap`.


## Requisitos

- Python 3
- `adb` (Android platform-tools)
- Celular Android con **depuración USB** o **depuración inalámbrica** activada

```bash
sudo apt install adb
pip install -r requirements.txt
```


## Uso

1. Conecta la computadora con el celular android usando el modo desarrollador y comprueba que aparece como `device`:
```bash
adb devices
```
2. Abre un nivel de Meowdoku en el celular.
3. Ejecuta el programa en la computadora:
```bash
python3 solver.py
```
4. Toca una sola vez en la parte superior central de la pantalla de juego (en medio de la puntuación y el nivel), para resolver automáticamente.
5. Presiona Ctrl+C para terminar el programa.


## Limitaciones

- Probado con un celular de 1264×2736 px. Con otras pantallas o diseños puede requerir ajustes (por ejemplo, el umbral `TOL` de color).
- El paso al siguiente nivel, la pantalla de victoria y los anuncios no están automatizados.
- Una lectura incorrecta del tablero podría colocar gatos en celdas erróneas y gastar vidas.


## Aviso

Proyecto personal sin relación con los desarrolladores de Meowdoku. Úsalo bajo tu propia responsabilidad.