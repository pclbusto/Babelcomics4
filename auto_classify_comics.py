#!/usr/bin/env python3
"""
Script para clasificar automáticamente comics físicos usando embeddings visuales.
Genera embeddings de las covers de comics sin clasificar y busca el ComicbookInfo más similar.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from entidades import Base
from entidades.comicbook_model import Comicbook
from entidades.comicbook_info_cover_model import ComicbookInfoCover
from entidades.comicbook_info_model import ComicbookInfo
from helpers.embedding_generator import get_embedding_generator


def auto_classify_comics(similarity_threshold=0.75, max_comics=None, auto_apply=False):
    """
    Clasifica automáticamente comics sin clasificar usando embeddings.

    Args:
        similarity_threshold: Umbral mínimo de similaridad (0-1) para aceptar una coincidencia
        max_comics: Máximo número de comics a procesar (None = todos)
        auto_apply: Si True, aplica automáticamente las clasificaciones. Si False, solo muestra sugerencias.
    """
    # Conectar a la base de datos
    db_path = os.path.join('data', 'babelcomics.db')
    if not os.path.exists(db_path):
        print(f"ERROR: No se encuentra la base de datos en {db_path}")
        return

    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Asegurar que la columna embedding existe en comicbooks
    try:
        with engine.begin() as conn:
            conn.execute("""
                ALTER TABLE comicbooks
                ADD COLUMN embedding TEXT
            """)
        print("Columna 'embedding' agregada a comicbooks")
    except:
        pass

    try:
        # Obtener generador de embeddings
        print("Inicializando generador de embeddings...")
        emb_gen = get_embedding_generator()

        # Obtener comics sin clasificar (id_comicbook_info vacío)
        comics_sin_clasificar = session.query(Comicbook).filter(
            (Comicbook.id_comicbook_info == '') | (Comicbook.id_comicbook_info == None)
        ).filter(
            Comicbook.en_papelera == False
        ).all()

        if max_comics:
            comics_sin_clasificar = comics_sin_clasificar[:max_comics]

        total_comics = len(comics_sin_clasificar)
        print(f"\nEncontrados {total_comics} comics sin clasificar")

        if total_comics == 0:
            print("No hay comics para clasificar!")
            return

        # Cargar todos los embeddings de ComicbookInfo covers en memoria
        print("\nCargando embeddings de covers existentes...")
        covers_con_embedding = session.query(ComicbookInfoCover).filter(
            ComicbookInfoCover.embedding != None,
            ComicbookInfoCover.embedding != ''
        ).all()

        if len(covers_con_embedding) == 0:
            print("ERROR: No hay covers con embeddings. Ejecuta primero generate_cover_embeddings.py")
            return

        print(f"Cargados {len(covers_con_embedding)} embeddings de covers")

        # Crear diccionario de cover_id -> comicbook_info_id
        cover_to_info = {cover.id_cover: cover.id_comicbook_info for cover in covers_con_embedding}

        # Crear lista de candidatos (id_cover, embedding)
        candidatos = [
            (cover.id_cover, emb_gen.json_to_embedding(cover.embedding))
            for cover in covers_con_embedding
        ]

        print(f"\n{'='*80}")
        print(f"Iniciando clasificación automática (umbral: {similarity_threshold})")
        print(f"{'='*80}\n")

        clasificados = 0
        omitidos = 0

        for i, comic in enumerate(comics_sin_clasificar, 1):
            try:
                # Obtener cover del comic
                cover_path = comic.obtener_cover()

                # Verificar que no sea la imagen por defecto
                if "Comic_sin_caratula" in cover_path or not os.path.exists(cover_path):
                    print(f"[{i}/{total_comics}] ⊘ {comic.nombre_archivo} - Sin thumbnail")
                    omitidos += 1
                    continue

                # Generar o usar embedding existente
                if comic.embedding:
                    embedding = emb_gen.json_to_embedding(comic.embedding)
                else:
                    print(f"[{i}/{total_comics}] Generando embedding para {comic.nombre_archivo}...")
                    embedding = emb_gen.generate_embedding(cover_path)
                    if embedding:
                        comic.embedding = emb_gen.embedding_to_json(embedding)

                if embedding is None:
                    print(f"[{i}/{total_comics}] ⊘ {comic.nombre_archivo} - Error generando embedding")
                    omitidos += 1
                    continue

                # Buscar la cover más similar
                resultado = emb_gen.find_most_similar(embedding, candidatos)

                if resultado is None:
                    print(f"[{i}/{total_comics}] ⊘ {comic.nombre_archivo} - Sin coincidencias")
                    omitidos += 1
                    continue

                cover_id, similarity = resultado
                comicbook_info_id = cover_to_info[cover_id]

                # Obtener información del ComicbookInfo
                info = session.query(ComicbookInfo).get(comicbook_info_id)

                if similarity >= similarity_threshold:
                    print(f"[{i}/{total_comics}] ✓ {comic.nombre_archivo}")
                    print(f"    → {info.titulo} #{info.numero} (similaridad: {similarity:.2%})")

                    if auto_apply:
                        comic.id_comicbook_info = str(comicbook_info_id)
                        clasificados += 1
                        print(f"    → APLICADO")
                    else:
                        print(f"    → SUGERIDO (usa --auto-apply para aplicar)")
                else:
                    print(f"[{i}/{total_comics}] ⊘ {comic.nombre_archivo}")
                    print(f"    → Mejor coincidencia: {info.titulo} #{info.numero} ({similarity:.2%})")
                    print(f"    → Similaridad bajo el umbral {similarity_threshold:.2%}")
                    omitidos += 1

            except Exception as e:
                print(f"[{i}/{total_comics}] ⊗ ERROR procesando {comic.nombre_archivo}: {e}")
                omitidos += 1

        # Guardar cambios
        if auto_apply and clasificados > 0:
            session.commit()
            print(f"\n✅ Clasificados {clasificados} comics automáticamente")
        elif clasificados > 0:
            session.rollback()
            print(f"\n💡 {clasificados} clasificaciones sugeridas (usa --auto-apply para aplicar)")

        print(f"⊘  {omitidos} comics omitidos (sin match o bajo umbral)")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Clasificación automática de comics usando embeddings visuales')
    parser.add_argument('--threshold', type=float, default=0.75,
                        help='Umbral mínimo de similaridad (0.0-1.0, default: 0.75)')
    parser.add_argument('--max', type=int, default=None,
                        help='Máximo número de comics a procesar')
    parser.add_argument('--auto-apply', action='store_true',
                        help='Aplicar automáticamente las clasificaciones (sin confirmación)')

    args = parser.parse_args()

    print("=" * 80)
    print("Clasificación Automática de Comics mediante Embeddings Visuales")
    print("=" * 80)

    auto_classify_comics(
        similarity_threshold=args.threshold,
        max_comics=args.max,
        auto_apply=args.auto_apply
    )
