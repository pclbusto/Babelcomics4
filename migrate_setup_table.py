#!/usr/bin/env python3
"""
Script de migración para actualizar la tabla setups con nuevos campos
y crear la tabla setup_directorios para soporte multi-directorio.
"""

import sqlite3
import base64
from pathlib import Path

def migrate_setup_table():
    """Migrar tabla setups con nuevos campos y estructura"""

    db_path = "data/babelcomics.db"

    if not Path(db_path).exists():
        print("❌ Error: No se encuentra la base de datos")
        return False

    print("🔄 Iniciando migración de tabla setups...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Obtener datos actuales antes de la migración
        print("📖 Leyendo configuración actual...")
        cursor.execute("SELECT * FROM setups LIMIT 1")
        current_setup = cursor.fetchone()

        if current_setup:
            print(f"✅ Configuración actual encontrada: setupkey={current_setup[0]}")
            # Datos actuales según esquema actual:
            # [setupkey, directorio_base, cantidad_comics_por_pagina, ultimo_volume_id_utilizado,
            #  ancho_arbol, expresion_regular_numero, ancho_thumbnail, modo_oscuro, actualizar_metadata, api_key]

            setupkey = current_setup[0]
            directorio_base = current_setup[1] or ""
            ultimo_volume_id = current_setup[3] or ""
            expresion_regular = current_setup[5] or r'.* (\d*) \('
            ancho_thumbnail_actual = current_setup[6] or 200
            modo_oscuro_actual = current_setup[7] or 0
            actualizar_metadata_actual = current_setup[8] or 0
            api_key_actual = current_setup[9] or ""

        else:
            print("⚠️  No hay configuración actual, usando valores por defecto")
            setupkey = 1
            directorio_base = ""
            ultimo_volume_id = ""
            expresion_regular = r'.* (\d*) \('
            ancho_thumbnail_actual = 200
            modo_oscuro_actual = 0
            actualizar_metadata_actual = 0
            api_key_actual = ""

        # 2. Crear tabla setup_directorios PRIMERO (para las FK)
        print("🗃️  Creando tabla setup_directorios...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS setup_directorios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setup_id INTEGER NOT NULL,
                directorio_path VARCHAR NOT NULL,
                activo BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY (setup_id) REFERENCES setups (setupkey)
            )
        """)

        # 3. Crear nueva tabla setups con estructura actualizada
        print("🔄 Creando nueva estructura de tabla setups...")
        cursor.execute("DROP TABLE IF EXISTS setups_new")

        cursor.execute("""
            CREATE TABLE setups_new (
                setupkey INTEGER PRIMARY KEY,
                ultimo_volume_id_utilizado VARCHAR,
                expresion_regular_numero VARCHAR NOT NULL DEFAULT '.* (\d*) \(',
                modo_oscuro BOOLEAN NOT NULL DEFAULT 0,
                actualizar_metadata BOOLEAN NOT NULL DEFAULT 0,
                api_key_encrypted VARCHAR NOT NULL DEFAULT '',
                rate_limit_interval REAL NOT NULL DEFAULT 0.5,
                thumbnail_size INTEGER NOT NULL DEFAULT 200,
                items_per_batch INTEGER NOT NULL DEFAULT 20,
                workers_concurrentes INTEGER NOT NULL DEFAULT 5,
                cache_thumbnails BOOLEAN NOT NULL DEFAULT 1,
                limpieza_automatica BOOLEAN NOT NULL DEFAULT 1
            )
        """)

        # 4. Encriptar API key (simple base64)
        api_key_encrypted = ""
        if api_key_actual:
            api_key_encrypted = base64.b64encode(api_key_actual.encode()).decode()
            print("🔐 API Key encriptada")

        # 5. Migrar datos a nueva estructura
        print("📦 Migrando datos existentes...")
        cursor.execute("""
            INSERT INTO setups_new (
                setupkey, ultimo_volume_id_utilizado, expresion_regular_numero,
                modo_oscuro, actualizar_metadata, api_key_encrypted,
                rate_limit_interval, thumbnail_size, items_per_batch,
                workers_concurrentes, cache_thumbnails, limpieza_automatica
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            setupkey,
            ultimo_volume_id,
            expresion_regular,
            modo_oscuro_actual,
            actualizar_metadata_actual,
            api_key_encrypted,
            0.5,  # rate_limit_interval
            ancho_thumbnail_actual,  # usar ancho_thumbnail actual como thumbnail_size
            20,   # items_per_batch
            5,    # workers_concurrentes
            1,    # cache_thumbnails
            1     # limpieza_automatica
        ))

        # 6. Migrar directorio_base a setup_directorios (si existe)
        if directorio_base and directorio_base.strip():
            print(f"📁 Migrando directorio base: {directorio_base}")
            cursor.execute("""
                INSERT INTO setup_directorios (setup_id, directorio_path, activo)
                VALUES (?, ?, 1)
            """, (setupkey, directorio_base.strip()))

        # 7. Reemplazar tabla original
        print("🔄 Actualizando estructura de base de datos...")
        cursor.execute("DROP TABLE setups")
        cursor.execute("ALTER TABLE setups_new RENAME TO setups")

        # 8. Verificar migración
        cursor.execute("SELECT COUNT(*) FROM setups")
        setup_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM setup_directorios")
        dir_count = cursor.fetchone()[0]

        conn.commit()
        conn.close()

        print("✅ Migración completada exitosamente!")
        print(f"   📊 Registros en setups: {setup_count}")
        print(f"   📊 Registros en setup_directorios: {dir_count}")

        return True

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_migration():
    """Verificar que la migración se completó correctamente"""
    print("\n🔍 Verificando migración...")

    try:
        conn = sqlite3.connect("data/babelcomics.db")
        cursor = conn.cursor()

        # Verificar estructura de setups
        cursor.execute("PRAGMA table_info(setups)")
        columns = cursor.fetchall()
        print("\n📋 Estructura actual de tabla setups:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        # Verificar datos migrados
        cursor.execute("SELECT * FROM setups")
        setup_data = cursor.fetchone()
        if setup_data:
            print(f"\n✅ Datos migrados:")
            print(f"   - setupkey: {setup_data[0]}")
            print(f"   - thumbnail_size: {setup_data[7]}")
            print(f"   - modo_oscuro: {setup_data[3]}")
            print(f"   - api_key_encrypted: {'***' if setup_data[5] else 'vacío'}")

        # Verificar setup_directorios
        cursor.execute("SELECT * FROM setup_directorios")
        dirs = cursor.fetchall()
        print(f"\n📁 Directorios configurados: {len(dirs)}")
        for dir_entry in dirs:
            print(f"   - {dir_entry[2]} (activo: {dir_entry[3]})")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Script de migración de tabla setups")
    print("=" * 50)

    if migrate_setup_table():
        verify_migration()
        print("\n🎉 Migración completada con éxito!")
    else:
        print("\n💥 Migración falló. Revisar errores arriba.")