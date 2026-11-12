# SAM · Extractor del ranking de ligas de TikTok LIVE

Saca los **@username reales** de los usuarios del ranking diario de una liga de TikTok LIVE
(por ejemplo "League D5", unos 100 puestos) y los guarda en Excel y `.txt`.

No usa APIs de TikTok, porque no hay ninguna pública para esto. Controla un **Android real conectado
por USB** con [`uiautomator2`](https://github.com/openatx/uiautomator2) y lee la jerarquía de la UI
(los textos que hay en pantalla) sin OCR. Hace lo mismo que haría una persona: toca a cada usuario,
lee su @username, vuelve atrás y baja la lista.

---

## 1. Contexto del problema

- En TikTok LIVE los creadores están en **ligas** (A1, B2, C3, D5, etc.). Cada liga tiene una
  **clasificación diaria** de unos 100 creadores que cambia minuto a minuto y se reinicia
  todos los días (alrededor de las 19:00).
- La lista solo muestra el **nombre visible** (que puede estar cortado o tener emojis), **no el @username**.
  Para obtener el @ hay que tocar a cada usuario.
- El objetivo es tener los 100 @username en cualquier momento del día sin copiarlos a mano.

## 2. Requisitos

| Qué | Detalle |
|---|---|
| PC | Windows (probado en Windows 10) o Mac, con Python 3.10 o superior |
| ADB | [Android platform-tools](https://developer.android.com/tools/releases/platform-tools). En esta PC está en `D:\USUARIO\Nueva carpeta - copia\platform-tools` y en el PATH del usuario |
| Android | Probado en un Redmi (`2209116AG`, 1080x2400). **Depuración USB** activada; en Xiaomi también "Depuración USB (ajustes de seguridad)" |
| TikTok | Instalado y con sesión iniciada (mejor con una cuenta secundaria), en inglés o en español |

## 3. Instalación (una sola vez)

```powershell
cd D:\USUARIO\Documentos\Workspace\SAM\extractor
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy config.example.json config.json
```

Conecta el celular, acepta el aviso "¿Permitir depuración USB?" y comprueba:

```powershell
adb devices                     # debe aparecer el celular como "device"
python main.py check            # "Conectado: <serial> ... pantalla 1080x2400"
```

La primera vez, `uiautomator2` instala sola una app auxiliar en el celular.

## 4. Uso

### 4.1 Dejar abierto el ranking (manual)
1. Abrir TikTok y entrar a cualquier **LIVE**.
2. Tocar la pastilla de arriba a la izquierda, debajo del nombre del anfitrión, que dice
   **"Daily No. X"** o **"League D5 No. X"** (id `tv_ranking_entrance_text`).
3. Se abre la hoja "Daily Ranking". Tocar la pestaña **"League XX"**.
   El script también la selecciona solo si la hoja está abierta.

### 4.2 Comandos

| Comando | Qué hace |
|---|---|
| `python main.py check` | Verifica la conexión con el celular |
| `python main.py liga` | Muestra la liga del ranking abierto (por ejemplo, `D5`) |
| `python main.py run` | Saca los 100 puestos de la liga abierta |
| `python main.py run 20` | Solo los primeros 20 (sirve para pruebas) |
| `python main.py run --liga D5` | Si la liga abierta no es la D5, va pasando de LIVE en LIVE hasta encontrar uno de la D5 y saca ese ranking |
| `python main.py run 100 --liga C3` | Combinación de las dos opciones |
| `python main.py inspect nombre` | Guarda una captura y la jerarquía de la UI en `dumps/` (para depurar o calibrar) |

En Windows conviene poner `$env:PYTHONIOENCODING="utf-8"` antes, para que los emojis se vean en la consola.

**Forma fácil (con consola visible):** doble clic en `extraer.bat`, o desde una terminal `extraer.bat --liga D5`.
Abre una ventana que muestra en vivo cada usuario extraído con su avance (`[37/100] ...`) y queda abierta al terminar.

**Seguimiento / log:** cada corrida escribe `logs/<fecha_hora>_run_....log` en tiempo real, con la hora en cada línea.
Para ver una corrida que se está ejecutando en segundo plano:
`Get-Content logs\<archivo>.log -Wait -Tail 20` (PowerShell). Si la última línea tiene la hora actual, sigue trabajando.

### 4.3 Resultado
En `output/`:
- `ranking_<LIGA>_<AAAA-MM-DD_HHMM>.xlsx` con las columnas **Liga, Puesto, Nombre visible, Username, Puntos**.
- `ranking_<LIGA>_<AAAA-MM-DD_HHMM>.txt` con un username por línea.

Si un puesto no se pudo leer, queda con el username vacío y se guarda una captura `dumps/sin_username_<puesto>.*`.

## 5. Cómo funciona por dentro

```
main.py             CLI (check / liga / inspect / run)
sam/config.py       carga config.json (o config.example.json)
sam/device.py       conexión uiautomator2 + dump_screen (png + xml)
sam/ranking.py      toda la lógica de navegación y lectura
sam/export.py       guarda Excel y txt
```

Flujo de `ranking.scrape()`:

1. **Liga.** Si se pasó `--liga` y la abierta es otra, se llama a `find_league()`:
   - lee la pastilla `tv_ranking_entrance_text`. Si dice "League XX" y no es la buscada, pasa al siguiente LIVE (swipe hacia arriba);
   - si solo dice "Daily No. X", abre la hoja, toca "League" y lee la liga de la pestaña;
   - si no coincide, cierra la hoja tocando el video y pasa al siguiente LIVE. Prueba hasta `max_lives_search` LIVEs.
2. `select_league_tab()` y `scroll_to_top()` para empezar en el puesto 1.
3. Lee las filas visibles del `RecyclerView` scrollable que contiene nodos `user_name`:
   el puesto es el número a la izquierda (x < 150), el nombre es `user_name` y los puntos son el texto a la derecha (x > 850).
4. Por cada fila nueva toca el centro de la fila y espera a reconocer la pantalla (`_wait_state`):
   - **`card`**: se abrió la tarjeta del usuario. El @username es el nodo `user_name` justo **encima** del texto
     "N followers · N following". Después hace `back` y vuelve a la lista.
   - **`live`**: el usuario estaba transmitiendo y TikTok entró a su LIVE. El script toca el nombre del anfitrión
     (arriba a la izquierda), lee la tarjeta, la cierra y **vuelve a abrir el ranking** desde la pastilla de ese LIVE
     (es la misma liga). Luego sigue desde donde iba, porque recuerda los puestos ya leídos.
     **No se usa `back` dentro de un LIVE**: en TikTok eso pasa a otro LIVE cualquiera.
5. Hace scroll dentro de la lista y repite hasta llegar a N puestos o hasta que no aparezcan filas nuevas.

### Selectores (calibrados el 2026-11-12, TikTok en inglés)
TikTok **ofusca** casi todos los resource-id (`tzo`, `ziy`, `ual`, etc.) y los cambia entre versiones.
Por eso el script solo usa ids estables y textos:
- `user_name`: nombre en las filas de la lista, @username en la tarjeta y nombre del anfitrión en un LIVE
- `tv_ranking_entrance_text`: la pastilla "Daily No. X" o "League D5 No. X"
- textos `followers` o `seguidores`, `League` o `Liga`
- la posición en pantalla (x/y), para distinguir el puesto, los puntos y la tarjeta

## 6. Configuración (`config.json`)

| Clave | Por defecto | Qué es |
|---|---|---|
| `device_serial` | `null` | Serial ADB si hay varios celulares conectados |
| `target_count` | `100` | Cuántos puestos sacar |
| `tap_delay_sec` | `1.5` | Espera después de tocar una fila |
| `back_delay_sec` | `1.2` | Espera después de cerrar la tarjeta |
| `scroll_delay_sec` | `1.2` | Espera después de cada scroll |
| `max_lives_search` | `80` | LIVEs que prueba al buscar una liga |
| `max_wait_outside_sec` | `900` | Cuánto espera (s) a que TikTok vuelva al frente antes de rendirse y guardar lo extraído |

### Protección contra llamadas y notificaciones (`sam/guard.py`)
Todos los toques, swipes y "atrás" pasan por `SafeDevice`, que antes de cada acción:
1. Revisa si hay una **llamada** sonando o en curso (`dumpsys telephony.registry`). Si la hay, espera sin tocar nada (así nunca contesta ni cuelga).
2. Revisa que la app al frente sea **TikTok** (`com.zhiliaoapp.musically`). Si no, espera 3 s y la vuelve a abrir con `app_start` (sin reiniciarla).
3. Revisa que el punto a tocar no esté tapado por un elemento de **otra app** (notificación flotante, diálogo). Si lo está, espera a que desaparezca; si sigue después de 20 s, no toca.

Si hubo una interrupción, la fila en curso se reintenta una vez y el ranking se vuelve a abrir. Si no logra volver a TikTok en `max_wait_outside_sec`, se detiene y **guarda lo extraído hasta ese momento**.
Recomendado igual: activar **No molestar** en el celular mientras corre.

Una corrida de 100 tarda unos 8 minutos. Para que sea menos notorio, se recomienda correrlo **cada 3 o 4 horas**.

## 7. Problemas comunes

| Síntoma | Causa / solución |
|---|---|
| `adb devices` vacío | Cable de solo carga, o falta aceptar el aviso de depuración USB en el celular |
| "No encuentro la lista del ranking" | La hoja no está abierta. Abrirla (sección 4.1) o usar `--liga` estando dentro de un LIVE |
| Empieza en un puesto que no es el 1 | Se corrige solo con `scroll_to_top()`. Si falla, subir la lista a mano |
| Muchos `sin_username` | TikTok cambió la UI. Correr `inspect`, revisar el xml en `dumps/` y ajustar `sam/ranking.py` (sección 5) |
| Termina en un LIVE de otra liga | Pasa si se usó `back` dentro de un LIVE. Volver a la liga a mano o usar `--liga` |
| Salen líneas `[guard] ...` | Hubo una llamada, notificación u otra app al frente; el script esperó y volvió a TikTok |
| Usernames repetidos | Se detecta como lectura de la tarjeta anterior y se reintenta el puesto (hasta 3 veces) |
| Termina con 99 filas | El ranking de liga muestra hasta el puesto 99; es normal |
| Emojis como `..` en la consola | Es solo la consola. En el Excel salen bien. Usar `PYTHONIOENCODING=utf-8` |

## 8. Pendiente / ideas
- [x] Corrida completa de 100 con usuarios en LIVE y búsqueda `--liga D5` (2026-11-12: 100 filas, 0 sin username, ~12 min)
- [ ] Probar la protección `guard.py` con una llamada / notificación real
- [ ] Programar la ejecución cada 3-4 horas (Programador de tareas de Windows)
- [ ] Guardar un historial (cada corrida en una hoja nueva o en una base de datos) y quitar duplicados entre corridas
- [ ] Lista de creadores de referencia por liga, para encontrar más rápido un LIVE de una liga específica
