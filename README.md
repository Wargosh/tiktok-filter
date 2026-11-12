# SAM

Extrae los @username de los 100 usuarios del ranking diario de una liga de TikTok LIVE
usando un Android conectado por USB, y los guarda en Excel y en un `.txt`.

No usa APIs de TikTok: controla el celular con `uiautomator2` como lo haria una persona
(toca a cada usuario, lee su @username, vuelve atras, baja la lista).

## Requisitos
- Windows o Mac con Python 3.10+
- Android con **Depuracion USB** activada (Ajustes > Acerca del telefono > tocar 7 veces "Numero de compilacion" > Opciones de desarrollador > Depuracion USB)
- ADB (Android platform-tools) en el PATH
- TikTok instalado y con sesion iniciada (de preferencia una cuenta secundaria)

## Instalacion
```
python -m venv .venv
.venv\Scripts\activate        # Mac: source .venv/bin/activate
pip install -r requirements.txt
python -m uiautomator2 init
copy config.example.json config.json
```

## Uso
1. `python main.py check` para confirmar que la PC ve el celular.
2. Abrir en el celular el ranking diario de la liga.
3. **Calibracion (solo la primera vez):** `python main.py inspect ranking`, luego tocar a un
   usuario y `python main.py inspect perfil`. Con esos archivos de `dumps/` se ajustan los
   `selectors` de `config.json`.
4. `python main.py run`, que genera `output/ranking_FECHA.xlsx` y `.txt`.

## Estado
- [x] Estructura base y exportacion a Excel/txt
- [ ] Calibrar selectores con la app real
- [ ] Abrir el ranking automaticamente desde el inicio de la app
- [ ] Programar ejecucion cada 3-4 horas (Programador de tareas de Windows / cron)
