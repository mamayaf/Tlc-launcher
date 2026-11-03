#!/usr/bin/env python3
"""
TCL Android TV Optimizer (Android TV 11 / MediaTek, poca RAM).
Funciona vía ADB por red. No requiere root. Todo es reversible con `restore`.

Uso:
  python3 tcl_optimizer.py --ip 192.168.1.50 info
  python3 tcl_optimizer.py --ip 192.168.1.50 optimize
  python3 tcl_optimizer.py --ip 192.168.1.50 list-apps
  python3 tcl_optimizer.py --ip 192.168.1.50 debloat      # usa debloat.txt
  python3 tcl_optimizer.py --ip 192.168.1.50 restore
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "estado_original.json")
DEBLOAT_FILE = os.path.join(HERE, "debloat.txt")

# (namespace, key, valor optimizado)
SETTINGS = [
    ("global", "window_animation_scale", "0.5"),
    ("global", "transition_animation_scale", "0.5"),
    ("global", "animator_duration_scale", "0.5"),
    ("global", "wifi_scan_always_enabled", "0"),
    ("global", "ble_scan_always_enabled", "0"),
    ("global", "network_recommendations_enabled", "0"),
]

DEVICE = None


def adb(*args, check=False):
    cmd = ["adb"] + (["-s", DEVICE] if DEVICE else []) + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"❌ Error: {' '.join(cmd)}\n{r.stderr.strip()}")
    return r.stdout.strip()


def sh(cmd):
    return adb("shell", cmd)


def connect(ip):
    global DEVICE
    if not shutil.which("adb"):
        sys.exit("❌ No se encontró 'adb'. Instala Android Platform Tools.")
    if ip:
        DEVICE = ip if ":" in ip else f"{ip}:5555"
        out = adb("connect", DEVICE)
        print(f"🔌 {out}")
        if "unauthorized" in out or "failed" in out or "cannot" in out:
            sys.exit("Acepta el diálogo de depuración en la TV y reintenta.")
    state = adb("get-state")
    if state != "device":
        sys.exit(f"❌ Dispositivo no listo (estado: {state or 'desconocido'}).")


def cmd_info(_):
    print("📺 Modelo:", sh("getprop ro.product.model"), "|", sh("getprop ro.product.device"))
    print("🤖 Android:", sh("getprop ro.build.version.release"))
    print("🧠 SoC:", sh("getprop ro.board.platform") or sh("getprop ro.hardware"))
    mem = sh("cat /proc/meminfo | head -3")
    print("💾 Memoria:\n  " + mem.replace("\n", "\n  "))
    print("📦 Almacenamiento /data:\n  " + sh("df -h /data | tail -1"))
    print("\n🔥 Top procesos por RAM (PSS):")
    out = sh("dumpsys meminfo | sed -n '/Total PSS by process/,/Total PSS by OOM/p' | head -20")
    print("  " + out.replace("\n", "\n  "))


def cmd_optimize(args):
    # Guarda estado original solo la primera vez para no pisarlo
    if not os.path.exists(STATE_FILE):
        state = {f"{ns}/{k}": sh(f"settings get {ns} {k}") for ns, k, _ in SETTINGS}
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        print(f"💾 Estado original guardado en {STATE_FILE}")

    for ns, k, v in SETTINGS:
        sh(f"settings put {ns} {k} {v}")
        print(f"✅ {ns}/{k} = {v}")

    print("🧹 Liberando caché de apps...")
    sh("pm trim-caches 999G")

    print("🔪 Cerrando procesos en segundo plano...")
    sh("am kill-all")

    if not args.skip_dexopt:
        print("⚙️  Compilando apps (dexopt). Puede tardar 5-20 min, no apagues la TV...")
        out = sh("cmd package bg-dexopt-job")
        print("   " + (out or "listo"))

    print("\n🎉 Listo. Reinicia la TV (o usa: adb reboot) para notar el cambio completo.")


def cmd_list_apps(_):
    sysapps = sh("pm list packages -s").replace("package:", "").split()
    user = sh("pm list packages -3").replace("package:", "").split()
    disabled = set(sh("pm list packages -d").replace("package:", "").split())
    print("📦 Apps de sistema (candidatas a debloat):")
    for p in sorted(sysapps):
        if any(x in p for x in ("tcl", "google", "netflix", "amazon", "facebook", "tv")):
            print(f"  {'[OFF] ' if p in disabled else '      '}{p}")
    print("\n📲 Apps instaladas por el usuario:")
    for p in sorted(user):
        print(f"  {'[OFF] ' if p in disabled else '      '}{p}")


def read_debloat():
    if not os.path.exists(DEBLOAT_FILE):
        sys.exit(f"❌ No existe {DEBLOAT_FILE}")
    with open(DEBLOAT_FILE) as f:
        return [l.split("#")[0].strip() for l in f if l.split("#")[0].strip()]


def cmd_debloat(_):
    installed = set(sh("pm list packages").replace("package:", "").split())
    for p in read_debloat():
        if p not in installed:
            print(f"⏭️  {p} (no instalado)")
            continue
        out = sh(f"pm disable-user --user 0 {p}")
        print(f"{'🚫' if 'disabled' in out else '⚠️ '} {p}: {out}")
    print("\nℹ️  Revertir: python3 tcl_optimizer.py restore")


def cmd_restore(_):
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
        for key, val in state.items():
            ns, k = key.split("/")
            if val in ("", "null"):
                sh(f"settings delete {ns} {k}")
            else:
                sh(f"settings put {ns} {k} {val}")
            print(f"↩️  {key} = {val}")
        os.remove(STATE_FILE)
    disabled = set(sh("pm list packages -d").replace("package:", "").split())
    for p in read_debloat() if os.path.exists(DEBLOAT_FILE) else []:
        if p in disabled:
            print(f"↩️  {p}: {sh(f'pm enable {p}')}")
    print("✅ Restaurado.")


def main():
    ap = argparse.ArgumentParser(description="Optimizador TCL Android TV vía ADB")
    ap.add_argument("--ip", help="IP de la TV (misma red). Omite si va por USB.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info", help="Diagnóstico de RAM/CPU/almacenamiento")
    o = sub.add_parser("optimize", help="Aplica optimizaciones seguras")
    o.add_argument("--skip-dexopt", action="store_true", help="No compilar apps")
    sub.add_parser("list-apps", help="Lista paquetes para decidir qué desactivar")
    sub.add_parser("debloat", help="Desactiva paquetes de debloat.txt")
    sub.add_parser("restore", help="Revierte todo")
    args = ap.parse_args()
    connect(args.ip)
    {"info": cmd_info, "optimize": cmd_optimize, "list-apps": cmd_list_apps,
     "debloat": cmd_debloat, "restore": cmd_restore}[args.cmd](args)


if __name__ == "__main__":
    main()
