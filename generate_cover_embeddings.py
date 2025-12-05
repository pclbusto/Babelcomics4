#!/usr/bin/env python3
"""
Script para generar embeddings de todas las covers de ComicbookInfo existentes.
Recorre todas las portadas en la base de datos y genera sus embeddings usando CLIP.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from entidades import Base
from entidades.comicbook_info_cover_model import ComicbookInfoCover
from helpers.embedding_generator import get_embedding_generator


def generate_all_cover_embeddings(batch_size=50):
    """
    Genera embeddings para todas las covers que no los tienen.

    Args:
        batch_size: Número de covers a procesar antes de hacer commit
    """
    # Conectar a la base de datos
    db_path = os.path.join('data', 'babelcomics.db')
    if not os.path.exists(db_path):
        print(f"ERROR: No se encuentra la base de datos en {db_path}")
        return

    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Asegurar que la columna embedding existe
    try:
        # Intentar agregar la columna si no existe
        with engine.begin() as conn:
            conn.execute("""
                ALTER TABLE comicbooks_info_covers
                ADD COLUMN embedding TEXT
            """)
        print("Columna 'embedding' agregada a comicbooks_info_covers")
    except:
        # La columna ya existe, continuar
        pass

    try:
        # Obtener generador de embeddings
        print("Inicializando generador de embeddings...")
        emb_gen = get_embedding_generator()

        # Obtener todas las covers sin embedding
        covers_sin_embedding = session.query(ComicbookInfoCover).filter(
            (ComicbookInfoCover.embedding == None) | (ComicbookInfoCover.embedding == '')
        ).all()

        total = len(covers_sin_embedding)
        print(f"\nEncontradas {total} covers sin embedding")

        if total == 0:
            print("Todas las covers ya tienen embeddings!")
            return

        procesadas = 0
        errores = 0

        for i, cover in enumerate(covers_sin_embedding, 1):
            try:
                # Obtener ruta de la imagen
                imagen_path = cover.obtener_ruta_local()

                # Verificar que no sea la imagen por defecto
                if "Comic_sin_caratula" in imagen_path:
                    print(f"[{i}/{total}] Omitiendo cover {cover.id_cover} (sin imagen descargada)")
                    continue

                # Verificar que el archivo existe
                if not os.path.exists(imagen_path):
                    print(f"[{i}/{total}] ERROR: No existe {imagen_path}")
                    errores += 1
                    continue

                # Generar embedding
                print(f"[{i}/{total}] Procesando cover {cover.id_cover}: {os.path.basename(imagen_path)}")
                embedding = emb_gen.generate_embedding(imagen_path)

                if embedding is not None:
                    # Guardar como JSON
                    cover.embedding = emb_gen.embedding_to_json(embedding)
                    procesadas += 1

                    # Commit cada batch_size items
                    if procesadas % batch_size == 0:
                        session.commit()
                        print(f"  → Guardadas {procesadas} covers")
                else:
                    errores += 1
                    print(f"  → ERROR generando embedding")

            except Exception as e:
                print(f"[{i}/{total}] ERROR procesando cover {cover.id_cover}: {e}")
                errores += 1

        # Commit final
        session.commit()

        print(f"\n✅ Proceso completado:")
        print(f"   - Covers procesadas: {procesadas}")
        print(f"   - Errores: {errores}")

    except Exception as e:
        print(f"ERROR: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Generador de Embeddings para Covers de ComicbookInfo")
    print("=" * 60)

    generate_all_cover_embeddings()
