#!/usr/bin/env python3
"""
Script de configuración inicial para Babelcomics4
Crea directorios necesarios, instala iconos y configura la base de datos
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def print_step(message):
    """Imprimir paso del setup con formato"""
    print(f"\n🔧 {message}")
    print("=" * (len(message) + 3))

def check_dependencies():
    """Verificar dependencias del sistema"""
    print_step("Verificando dependencias")

    dependencies = {
        'magick': 'ImageMagick (para redimensionar iconos)',
        'python3': 'Python 3',
        'pip': 'pip (gestor de paquetes Python)'
    }

    missing = []
    for cmd, desc in dependencies.items():
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
            print(f"✅ {desc} - OK")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {desc} - FALTANTE")
            missing.append(cmd)

    if missing:
        print(f"\n⚠️ Instala las dependencias faltantes:")
        if 'magick' in missing:
            print("   sudo pacman -S imagemagick  # Arch Linux")
            print("   sudo apt install imagemagick  # Ubuntu/Debian")
        return False

    return True

def create_directories():
    """Crear estructura de directorios necesarios"""
    print_step("Creando directorios")

    directories = [
        # Directorios de datos
        "data",
        "data/thumbnails",
        "data/thumbnails/comics",
        "data/thumbnails/volumes",
        "data/thumbnails/publishers",
        "data/thumbnails/comicbookinfo_issues",

        # Directorios de logs
        "logs",

        # Directorios de configuración
        "config",

        # Directorios de backup
        "backup"
    ]

    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 {directory}")

    print("✅ Estructura de directorios creada")

def install_icons():
    """Instalar iconos en el sistema"""
    print_step("Instalando iconos del sistema")

    icon_source = Path("images/icon.png")
    if not icon_source.exists():
        print(f"❌ No se encontró el icono fuente: {icon_source}")
        return False

    # Crear directorios de iconos
    icon_base = Path.home() / ".local/share/icons/hicolor"
    sizes = ["48x48", "64x64", "128x128", "256x256", "scalable"]

    for size in sizes[:-1]:  # Excluir scalable por ahora
        icon_dir = icon_base / size / "apps"
        icon_dir.mkdir(parents=True, exist_ok=True)

        target_path = icon_dir / "babelcomics4.png"

        if size == "128x128" or size == "256x256":
            # Copiar directamente para tamaños grandes
            shutil.copy2(icon_source, target_path)
            print(f"📎 {size}/apps/babelcomics4.png (copiado)")
        else:
            # Redimensionar para tamaños pequeños
            try:
                cmd = [
                    "magick", str(icon_source),
                    "-resize", size,
                    str(target_path)
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"🔄 {size}/apps/babelcomics4.png (redimensionado)")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error redimensionando {size}: {e}")
                return False

    # Instalar icono SVG escalable si existe
    svg_source = Path("images/icon.svg")
    if svg_source.exists():
        scalable_dir = icon_base / "scalable/apps"
        scalable_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(svg_source, scalable_dir / "babelcomics4.svg")
        print("🎨 scalable/apps/babelcomics4.svg (SVG)")

    # Actualizar cache de iconos
    try:
        subprocess.run(["gtk-update-icon-cache", str(icon_base)],
                      capture_output=True, check=False)
        print("🔄 Cache de iconos actualizado")
    except:
        print("⚠️ No se pudo actualizar el cache de iconos (no crítico)")

    print("✅ Iconos instalados correctamente")
    return True

def setup_database():
    """Configurar base de datos"""
    print_step("Configurando base de datos")

    try:
        # Importar módulos necesarios
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from entidades import Base

        # Crear base de datos
        db_path = "data/babelcomics.db"
        engine = create_engine(f'sqlite:///{db_path}', echo=False)

        # Crear todas las tablas
        Base.metadata.create_all(engine)

        # Verificar que la base de datos funciona
        Session = sessionmaker(bind=engine)
        session = Session()
        session.close()

        print(f"✅ Base de datos creada: {db_path}")
        return True

    except Exception as e:
        print(f"❌ Error configurando base de datos: {e}")
        return False

def install_python_dependencies():
    """Instalar dependencias de Python"""
    print_step("Verificando dependencias de Python")

    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Dependencias de Python instaladas")
                return True
            else:
                print(f"❌ Error instalando dependencias: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error ejecutando pip: {e}")
            return False
    else:
        print("⚠️ No se encontró requirements.txt")
        return True

def create_desktop_file():
    """Crear archivo .desktop para el menú de aplicaciones"""
    print_step("Creando entrada en el menú de aplicaciones")

    desktop_dir = Path.home() / ".local/share/applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    desktop_file = desktop_dir / "babelcomics4.desktop"
    current_dir = Path.cwd().absolute()

    desktop_content = f"""[Desktop Entry]
Name=Babelcomics4
Comment=Gestor completo de colección de comics digitales
Exec=python3 {current_dir}/Babelcomic4.py
Icon=babelcomics4
Terminal=false
Type=Application
Categories=Graphics;Office;AudioVideo;
MimeType=application/x-cbz;application/x-cbr;application/pdf;
StartupNotify=true
"""

    try:
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)

        # Hacer ejecutable
        desktop_file.chmod(0o755)

        print(f"✅ Archivo desktop creado: {desktop_file}")
        print("   La aplicación aparecerá en el menú de aplicaciones")
        return True

    except Exception as e:
        print(f"❌ Error creando archivo desktop: {e}")
        return False

def create_startup_script():
    """Crear script de inicio"""
    print_step("Creando script de inicio")

    current_dir = Path.cwd().absolute()
    script_path = current_dir / "babelcomics4.sh"

    script_content = f"""#!/bin/bash
# Script de inicio para Babelcomics4

cd "{current_dir}"

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Entorno virtual activado"
fi

# Verificar dependencias básicas
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado"
    exit 1
fi

# Ejecutar aplicación
echo "🚀 Iniciando Babelcomics4..."
python3 Babelcomic4.py

# Desactivar entorno virtual
if [ -d ".venv" ]; then
    deactivate
fi
"""

    try:
        with open(script_path, 'w') as f:
            f.write(script_content)

        # Hacer ejecutable
        script_path.chmod(0o755)

        print(f"✅ Script de inicio creado: {script_path}")
        print("   Puedes ejecutar: ./babelcomics4.sh")
        return True

    except Exception as e:
        print(f"❌ Error creando script de inicio: {e}")
        return False

def main():
    """Función principal del setup"""
    print("🎯 BABELCOMICS4 SETUP")
    print("=" * 50)
    print("Este script configurará tu instalación de Babelcomics4")

    # Lista de pasos
    steps = [
        ("Verificar dependencias", check_dependencies),
        ("Crear directorios", create_directories),
        ("Instalar dependencias Python", install_python_dependencies),
        ("Configurar base de datos", setup_database),
        ("Instalar iconos", install_icons),
        ("Crear entrada en menú", create_desktop_file),
        ("Crear script de inicio", create_startup_script)
    ]

    success_count = 0
    total_steps = len(steps)

    for step_name, step_func in steps:
        try:
            if step_func():
                success_count += 1
            else:
                print(f"⚠️ {step_name} falló, pero continuando...")
        except Exception as e:
            print(f"❌ Error en {step_name}: {e}")

    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DEL SETUP")
    print("=" * 50)
    print(f"✅ Pasos completados: {success_count}/{total_steps}")

    if success_count == total_steps:
        print("\n🎉 ¡Setup completado exitosamente!")
        print("\n📋 Próximos pasos:")
        print("   1. Ejecuta: ./babelcomics4.sh")
        print("   2. O busca 'Babelcomics4' en el menú de aplicaciones")
        print("   3. Configura tu directorio de comics en la aplicación")
    else:
        print(f"\n⚠️ Setup completado con {total_steps - success_count} errores")
        print("   Revisa los mensajes de error arriba")
        print("   Puedes intentar ejecutar la aplicación manualmente:")
        print("   python3 Babelcomic4.py")

    print("\n📚 Para más información, consulta la documentación")
    print("   https://github.com/pedro/babelcomics4/wiki")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)