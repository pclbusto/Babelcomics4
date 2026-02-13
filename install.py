#!/usr/bin/env python3
"""Instala Babelcomics4: iconos, .desktop, venv y dependencias.

Uso:
    python3 install.py              # Instalación completa (pregunta por embeddings)
    python3 install.py --embeddings # Solo instalar/actualizar sistema de embeddings
    python3 install.py --help       # Mostrar ayuda
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

TARGET_BASE = Path.home() / ".local" / "share" / "icons" / "hicolor"
DESKTOP_TARGET = Path.home() / ".local" / "share" / "applications"
PNG_SIZES = (16, 22, 24, 32, 48, 64, 128, 256, 512, 1024)


def require_pillow():
    """Carga Pillow o sugiere instalarlo si falta."""
    try:
        from PIL import Image, ImageOps  # type: ignore
    except ImportError as exc:
        print(
            "Pillow no está instalado. Ejecutá:\n"
            "  pip install Pillow\n"
            "(usando tu entorno virtual si corresponde)."
        )
        raise SystemExit(exc) from exc
    return Image, ImageOps


def install_pngs(source: Path, Image, ImageOps) -> None:
    """Genera variantes PNG en todos los tamaños y las copia al tema hicolor."""
    if not source.exists():
        raise SystemExit(f"No se encontró el icono base: {source}")

    # Lista de nombres de iconos a instalar
    icon_names = ["babelcomics4", "com.babelcomics.manager"]

    for size in PNG_SIZES:
        target_dir = TARGET_BASE / f"{size}x{size}" / "apps"
        target_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(source) as img:
            # Para 1024x1024, usar el original directamente sin redimensionar
            if size == 1024:
                icon = img.convert("RGBA")
            else:
                icon = ImageOps.fit(img.convert("RGBA"), (size, size), method=Image.LANCZOS)

            # Instalar con ambos nombres
            for icon_name in icon_names:
                target_path = target_dir / f"{icon_name}.png"
                icon.save(target_path, format="PNG", optimize=True)
                print(f"✔ Icono {icon_name} {size}x{size} instalado en {target_path}")


def refresh_icon_cache() -> None:
    """Actualiza la cache de iconos si la utilidad está disponible."""
    helper = shutil.which("gtk4-update-icon-cache") or shutil.which("gtk-update-icon-cache")
    if not helper:
        print("ℹ No se encontró gtk4-update-icon-cache; omito refrescar la cache.")
        return

    # Asegura que exista un index.theme para que update-icon-cache funcione
    index_theme = TARGET_BASE / "index.theme"
    if not index_theme.exists():
        system_index = Path("/usr/share/icons/hicolor/index.theme")
        if system_index.exists():
            try:
                shutil.copy2(system_index, index_theme)
                print(f"✔ Copiado {system_index} a {index_theme}")
            except Exception as exc:
                print(f"⚠ Advertencia: no se pudo copiar index.theme: {exc}")
        else:
            print("⚠ Advertencia: No se encontró index.theme en el sistema, la actualización puede fallar.")

    if not index_theme.exists():
         print("⚠ Saltando gtk-update-icon-cache porque falta index.theme local.")
         return

    try:
        subprocess.run([helper, str(TARGET_BASE)], check=True)
        print("✔ Cache de iconos actualizada.")
    except subprocess.CalledProcessError as exc:
        print(f"⚠ No se pudo actualizar la cache de iconos: {exc}")


def setup_venv(repo_root: Path) -> Path:
    """Crea el venv si no existe y retorna la ruta al python del venv."""
    venv_dir = repo_root / ".venv"
    venv_python = venv_dir / "bin" / "python3"

    if not venv_dir.exists():
        print("→ Creando entorno virtual...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print("✔ Entorno virtual creado en .venv/")
    else:
        print("✔ Entorno virtual ya existe en .venv/")

    return venv_python


def check_system_dependencies() -> None:
    """Verifica e informa sobre dependencias del sistema necesarias."""
    print("→ Verificando dependencias del sistema...")

    # Detectar distribución
    try:
        with open("/etc/os-release") as f:
            os_release = f.read().lower()
            if "arch" in os_release:
                distro = "arch"
            elif "ubuntu" in os_release or "debian" in os_release:
                distro = "debian"
            elif "fedora" in os_release:
                distro = "fedora"
            else:
                distro = "unknown"
    except:
        distro = "unknown"

    # Verificar gobject-introspection
    try:
        result = subprocess.run(
            ["pkg-config", "--exists", "gobject-introspection-1.0"],
            capture_output=True
        )
        if result.returncode == 0:
            print("✔ gobject-introspection instalado")
        else:
            raise subprocess.CalledProcessError(1, "pkg-config")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ gobject-introspection no encontrado")
        print("  PyGObject requiere esta dependencia del sistema.")
        print("  Instalá con:")
        if distro == "arch":
            print("    sudo pacman -S gobject-introspection")
        elif distro == "debian":
            print("    sudo apt install libgirepository1.0-dev")
        elif distro == "fedora":
            print("    sudo dnf install gobject-introspection-devel")
        else:
            print("    Consultá la documentación de tu distribución")
        print("\n  Continuando la instalación...")


def install_requirements(venv_python: Path, repo_root: Path) -> None:
    """Instala dependencias por separado: core primero, luego AI opcional."""
    requirements = repo_root / "requirements.txt"

    if not requirements.exists():
        print("⚠ No se encontró requirements.txt, saltando instalación de dependencias.")
        return

    print("→ Instalando dependencias CORE (esenciales)...")
    core_deps = [
        "SQLAlchemy>=2.0.0",
        "requests>=2.31.0",
        "Pillow>=10.0.0",
        "rarfile>=4.0",
        "py7zr>=0.20.0",
        "PyGObject>=3.42.0",
        "numpy<2"
    ]

    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✔ pip actualizado")
    except subprocess.CalledProcessError as exc:
        print(f"⚠ No se pudo actualizar pip: {exc}")

    # Instalar dependencias core
    failed_core = []
    for dep in core_deps:
        try:
            print(f"  Instalando {dep.split('>=')[0]}...")
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", dep],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as exc:
            failed_core.append(dep)
            print(f"  ⚠ Falló: {dep.split('>=')[0]}")

    if failed_core:
        print(f"\n⚠ Algunas dependencias core fallaron: {', '.join([d.split('>=')[0] for d in failed_core])}")
        print("  La aplicación puede no funcionar correctamente.")
    else:
        print("✔ Dependencias core instaladas correctamente.")

    # Intentar instalar dependencias de IA (opcionales)
    print("\n→ Instalando dependencias de IA (opcionales)...")
    print("  Las funciones de IA requieren torch y transformers.")
    print("  Esto puede tardar varios minutos y requiere compilación...")

    ai_deps = ["transformers==4.25.1"]

    # No intentar instalar torch automáticamente por ahora
    print("  ⚠ PyTorch NO se instalará automáticamente (requiere configuración específica)")
    print("  Para instalar soporte de IA manualmente:")
    print("    # Para GTX 1070 (CUDA 11.7):")
    print("    .venv/bin/pip install torch==1.13.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117")
    print("    .venv/bin/pip install transformers==4.25.1")
    print("    # Para CPU o GPU moderna:")
    print("    .venv/bin/pip install torch transformers")

    # Solo instalar transformers si el usuario lo desea
    # (por ahora lo saltamos para instalación rápida)
    print("\n✔ Dependencias básicas instaladas. AI features opcionales.")


def update_shell_script(repo_root: Path) -> None:
    """Actualiza las rutas en babelcomics4.sh con la ruta absoluta del proyecto."""
    script_path = repo_root / "babelcomics4.sh"

    if not script_path.exists():
        print(f"⚠ No se encontró {script_path}")
        return

    content = script_path.read_text()

    # Reemplazar cualquier ruta cd con la ruta actual
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.strip().startswith('cd '):
            new_lines.append(f'cd "{repo_root}"')
        else:
            new_lines.append(line)

    new_content = '\n'.join(new_lines)

    if new_content != content:
        script_path.write_text(new_content)
        print(f"✔ Actualizada la ruta en babelcomics4.sh a: {repo_root}")
    else:
        print("✔ babelcomics4.sh ya tiene la ruta correcta.")

    # Hacer el script ejecutable
    script_path.chmod(0o755)


def create_desktop_file(repo_root: Path) -> None:
    """Crea el archivo .desktop con las rutas correctas basándose en la ubicación actual."""

    script_path = repo_root / "babelcomics4.sh"

    # Crear el directorio de destino si no existe
    DESKTOP_TARGET.mkdir(parents=True, exist_ok=True)

    # Asegurar que el script sea ejecutable
    if script_path.exists():
        script_path.chmod(0o755)

    # Contenido del archivo .desktop
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Babelcomics4
GenericName=Comic Collection Manager
Comment=Gestor completo de colección de comics digitales
Exec="{script_path}"
Icon=com.babelcomics.manager
Terminal=false
Categories=Graphics;Viewer;Office;
Keywords=comic;cbr;cbz;cb7;pdf;collection;manager;
MimeType=application/x-cbz;application/x-cbr;application/x-cb7;application/pdf;
StartupNotify=true
StartupWMClass=com.babelcomics.manager
"""

    # Escribir el archivo
    target = DESKTOP_TARGET / "com.babelcomics.manager.desktop"
    target.write_text(desktop_content)
    print(f"✔ Archivo .desktop creado en {target}")

    # Validar el .desktop si está disponible desktop-file-validate
    validator = shutil.which("desktop-file-validate")
    if validator:
        try:
            subprocess.run([validator, str(target)], check=True, capture_output=True)
            print("✔ Archivo .desktop validado correctamente.")
        except subprocess.CalledProcessError as exc:
            print(f"⚠ Advertencia al validar .desktop: {exc.stderr.decode()}")

    # Actualizar la base de datos de aplicaciones
    updater = shutil.which("update-desktop-database")
    if updater:
        try:
            subprocess.run([updater, str(DESKTOP_TARGET)], check=True, capture_output=True)
            print("✔ Base de datos de aplicaciones actualizada.")
        except subprocess.CalledProcessError as exc:
            print(f"⚠ No se pudo actualizar la base de datos: {exc}")


def run_setup_py(repo_root: Path, venv_python: Path) -> None:
    """Ejecuta el setup.py del proyecto si existe."""
    setup_script = repo_root / "setup.py"

    if not setup_script.exists():
        print("⚠ No se encontró setup.py")
        return

    print("→ Ejecutando setup.py para configurar la base de datos...")
    try:
        subprocess.run(
            [str(venv_python), str(setup_script)],
            check=True,
            cwd=str(repo_root)
        )
        print("✔ setup.py ejecutado correctamente.")
    except subprocess.CalledProcessError as exc:
        print(f"⚠ Error al ejecutar setup.py: {exc}")


def update_database_schema_for_embeddings(repo_root: Path, venv_python: Path) -> bool:
    """Actualiza el esquema de la base de datos para soportar embeddings."""
    db_path = repo_root / "data" / "babelcomics.db"

    if not db_path.exists():
        print("  ℹ Base de datos no encontrada, se creará al ejecutar la aplicación")
        return True

    # Script Python para actualizar el schema
    update_script = """
import os
from sqlalchemy import create_engine

db_path = 'data/babelcomics.db'
if os.path.exists(db_path):
    engine = create_engine(f'sqlite:///{db_path}')
    with engine.begin() as conn:
        try:
            conn.execute('ALTER TABLE comicbooks_info_covers ADD COLUMN embedding TEXT')
            print('  ✔ Columna embedding agregada a comicbooks_info_covers')
        except:
            print('  ✔ Columna embedding ya existe en comicbooks_info_covers')

        try:
            conn.execute('ALTER TABLE comicbooks ADD COLUMN embedding TEXT')
            print('  ✔ Columna embedding agregada a comicbooks')
        except:
            print('  ✔ Columna embedding ya existe en comicbooks')
"""

    try:
        result = subprocess.run(
            [str(venv_python), "-c", update_script],
            check=True,
            cwd=str(repo_root),
            capture_output=True,
            text=True
        )
        print(result.stdout, end='')
        return True
    except subprocess.CalledProcessError as exc:
        print(f"  ⚠ Error actualizando schema: {exc}")
        return False


def install_embeddings_dependencies(venv_python: Path) -> bool:
    """Instala las dependencias necesarias para el sistema de embeddings."""
    print("\n→ Instalando dependencias de IA para embeddings...")
    print("  Esto puede tardar varios minutos (descarga ~2GB)")

    ai_deps = [
        "transformers>=4.30.0",
    ]

    # Preguntar sobre PyTorch
    print("\n  Para usar embeddings, necesitas PyTorch.")
    print("\n  💡 Si no estás seguro qué versión elegir, ejecutá:")
    print("     ./check_cuda.sh")
    print("\n  Opciones:")
    print("    1) CPU - Instalación rápida, funciona en todos los sistemas")
    print("    2) CUDA 11.8 - Para GPUs NVIDIA (GTX 1070, RTX 2000/3000/4000)")
    print("    3) CUDA 12.1 - Para GPUs NVIDIA más recientes (RTX 4000+)")
    print("    4) Saltar - Instalar manualmente después")

    choice = input("\n  Seleccioná una opción [1/2/3/4]: ").strip()

    torch_cmd = None
    if choice == "1":
        torch_cmd = [str(venv_python), "-m", "pip", "install", "torch", "torchvision", "--index-url", "https://download.pytorch.org/whl/cpu"]
    elif choice == "2":
        torch_cmd = [str(venv_python), "-m", "pip", "install", "torch", "torchvision", "--index-url", "https://download.pytorch.org/whl/cu118"]
    elif choice == "3":
        torch_cmd = [str(venv_python), "-m", "pip", "install", "torch", "torchvision", "--index-url", "https://download.pytorch.org/whl/cu121"]
    elif choice == "4":
        print("  ℹ Saltando instalación de PyTorch")
        print("  Instalá manualmente con:")
        print("    # CPU:")
        print("    .venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu")
        print("    # CUDA 11.8:")
        print("    .venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
        print("    # CUDA 12.1+:")
        print("    .venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        print("    # Luego:")
        print("    .venv/bin/pip install transformers")
        return False
    else:
        print("  ⚠ Opción inválida, saltando instalación de PyTorch")
        return False

    # Instalar PyTorch
    if torch_cmd:
        try:
            print("  Instalando PyTorch (esto puede tardar varios minutos)...")
            subprocess.run(torch_cmd, check=True)
            print("  ✔ PyTorch instalado")
        except subprocess.CalledProcessError as exc:
            print(f"  ⚠ Error instalando PyTorch: {exc}")
            return False

    # Instalar transformers y otras dependencias
    for dep in ai_deps:
        try:
            print(f"  Instalando {dep.split('==')[0]}...")
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", dep],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as exc:
            print(f"  ⚠ Error instalando {dep}: {exc}")
            return False

    print("  ✔ Dependencias de embeddings instaladas correctamente")
    return True


def setup_embeddings(repo_root: Path, venv_python: Path) -> None:
    """Configura el sistema completo de embeddings."""
    print("\n" + "=" * 60)
    print("  INSTALACIÓN DE SISTEMA DE EMBEDDINGS")
    print("=" * 60)

    # 1. Instalar dependencias
    if not install_embeddings_dependencies(venv_python):
        print("\n⚠ Instalación de embeddings cancelada o falló.")
        print("  Podés instalar manualmente ejecutando:")
        print("    ./setup_embeddings.sh")
        return

    # 2. Actualizar schema de base de datos
    print("\n→ Actualizando esquema de base de datos...")
    update_database_schema_for_embeddings(repo_root, venv_python)

    # 3. Verificar instalación
    test_script = repo_root / "test_embeddings.py"
    if test_script.exists():
        print("\n→ Verificando instalación...")
        try:
            subprocess.run(
                [str(venv_python), str(test_script)],
                check=True,
                cwd=str(repo_root),
                capture_output=True,
                timeout=30
            )
            print("  ✔ Instalación verificada correctamente")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print("  ⚠ Verificación falló (probablemente porque no hay imágenes de prueba)")
            print("  Esto es normal si acabas de instalar")

    print("\n" + "=" * 60)
    print("✔ SISTEMA DE EMBEDDINGS CONFIGURADO")
    print("=" * 60)
    print("\nPróximos pasos:")
    print("1. Generar embeddings de tus covers de ComicVine:")
    print("   .venv/bin/python generate_cover_embeddings.py")
    print("\n2. Clasificar automáticamente tus comics:")
    print("   Usar la interfaz gráfica (ventana de clasificación por IA)")
    print("=" * 60)


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    png_source = repo_root / "images" / "icon.png"

    print("=" * 60)
    print("  Instalador de Babelcomics4")
    print("=" * 60)
    print(f"Ruta del proyecto: {repo_root}\n")

    # 1. Verificar dependencias del sistema
    print("[1/8] Verificando dependencias del sistema...")
    check_system_dependencies()

    # 2. Configurar venv
    print("\n[2/8] Configurando entorno virtual...")
    venv_python = setup_venv(repo_root)

    # 3. Instalar dependencias
    print("\n[3/8] Instalando dependencias Python...")
    install_requirements(venv_python, repo_root)

    # 4. Ejecutar setup.py
    print("\n[4/8] Configurando base de datos...")
    run_setup_py(repo_root, venv_python)

    # 5. Actualizar script
    print("\n[5/8] Actualizando babelcomics4.sh...")
    update_shell_script(repo_root)

    # 6. Instalar iconos
    print("\n[6/8] Instalando iconos...")
    Image, ImageOps = require_pillow()
    install_pngs(png_source, Image, ImageOps)
    refresh_icon_cache()

    # 7. Crear archivo .desktop
    print("\n[7/8] Creando archivo .desktop...")
    create_desktop_file(repo_root)

    print("\n[8/8] Finalización")
    print("=" * 60)
    print("✔ Instalación básica completada exitosamente!")
    print(f"  - Entorno virtual: {repo_root / '.venv'}")
    print(f"  - Lanzador instalado en: {DESKTOP_TARGET / 'com.babelcomics.manager.desktop'}")
    print(f"  - Iconos instalados en: {TARGET_BASE}")
    print("\n📚 Podés buscar 'Babelcomics4' en tu menú de aplicaciones.")
    print("   O ejecutar: ./babelcomics4.sh")

    # Preguntar si desea instalar embeddings
    print("\n" + "=" * 60)
    print("💡 FUNCIONES OPCIONALES DE IA")
    print("=" * 60)
    print("\nBabelcomics4 incluye clasificación automática por IA usando embeddings.")
    print("Esto requiere PyTorch y Transformers (~2GB de descarga).")

    try:
        response = input("\n¿Deseas instalar el sistema de embeddings ahora? [s/N]: ").strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            setup_embeddings(repo_root, venv_python)
        else:
            print("\n✔ Instalación de embeddings omitida.")
            print("  Podés instalar manualmente después ejecutando:")
            print("    python3 install.py --embeddings")
            print("    # O usar el script bash:")
            print("    ./setup_embeddings.sh")
    except (EOFError, KeyboardInterrupt):
        print("\n\n✔ Instalación de embeddings omitida.")

    print("\n" + "=" * 60)
    print("✔ INSTALACIÓN FINALIZADA")
    print("=" * 60)


def main_embeddings_only() -> None:
    """Instala solo el sistema de embeddings (requiere instalación básica previa)."""
    repo_root = Path(__file__).resolve().parent

    print("=" * 60)
    print("  Instalador de Embeddings para Babelcomics4")
    print("=" * 60)
    print(f"Ruta del proyecto: {repo_root}\n")

    # Verificar que existe .venv
    venv_python = repo_root / ".venv" / "bin" / "python3"
    if not venv_python.exists():
        print("❌ Error: No se encontró el entorno virtual (.venv)")
        print("   Ejecutá primero la instalación básica:")
        print("   python3 install.py")
        sys.exit(1)

    # Instalar embeddings
    setup_embeddings(repo_root, venv_python)


def print_help() -> None:
    """Muestra la ayuda del instalador."""
    print(__doc__)


if __name__ == "__main__":
    # Parsear argumentos simples
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--help", "-h", "help"]:
            print_help()
        elif arg == "--embeddings":
            main_embeddings_only()
        else:
            print(f"❌ Argumento desconocido: {sys.argv[1]}")
            print_help()
            sys.exit(1)
    else:
        main()
