# TCL TV Optimizer 📺⚡

Optimizador vía **ADB** para TV TCL con Android TV 11 (MediaTek, `V8-R51MT05`, kernel 4.14). Sin root, todo reversible.

## Qué hace
| Acción | Efecto |
|---|---|
| Animaciones a 0.5x | UI se siente ~2x más rápida |
| `pm trim-caches` | Libera almacenamiento (crítico si /data está casi lleno) |
| `am kill-all` | Cierra procesos en segundo plano |
| `bg-dexopt-job` | Compila apps AOT → arranque más rápido |
| Desactiva escaneo WiFi/BLE permanente | Menos CPU/ruido de fondo |
| `debloat` | Desactiva apps preinstaladas que no uses (libera RAM) |
| `uninstall` | Desinstala para el usuario 0 (`pm uninstall -k --user 0`): libera RAM y espacio |

## Preparación (TV)
1. Ajustes → Sistema → Acerca de → pulsa **Compilación** 7 veces.
2. Ajustes → Sistema → Opciones de desarrollador → **Depuración USB / ADB por red** ON.
3. Anota la IP de la TV (Ajustes → Red).

## Uso (PC con `adb` y Python 3)
```bash
python3 tcl_optimizer.py --ip 192.168.1.50 info        # diagnóstico
python3 tcl_optimizer.py --ip 192.168.1.50 optimize    # optimiza
python3 tcl_optimizer.py --ip 192.168.1.50 list-apps   # ver paquetes
# edita debloat.txt
python3 tcl_optimizer.py --ip 192.168.1.50 debloat
python3 tcl_optimizer.py --ip 192.168.1.50 uninstall   # o desinstalar (libera espacio)
python3 tcl_optimizer.py --ip 192.168.1.50 restore     # revertir todo
```

## Desde el celular Android 📱 (Termux)
1. Instala **Termux** desde F-Droid (la de Play Store está desactualizada).
2. En Termux:
```bash
pkg update && pkg install -y android-tools python git
git clone https://github.com/mamayaf/Tlc-launcher && cd Tlc-launcher
git checkout ccr-6213a22d-7epqy2
python tcl_optimizer.py --ip <IP_TV> info
```
El celular y la TV deben estar en la misma red WiFi.
Acepta el diálogo "¿Permitir depuración?" en la TV la primera vez.

## Mayor ganancia extra 🚀
- **Launcher ligero**: el launcher stock es lo más pesado. Instala *Projectivy Launcher* o *FLauncher* (Play Store) y desactiva las recomendaciones del stock.
- Mantén ≥ 1 GB libre en almacenamiento.
- Desinstala actualizaciones de apps que no uses (Ajustes → Apps).
- Reinicia la TV 1 vez por semana (las TCL no apagan realmente en standby).
