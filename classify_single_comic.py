#!/usr/bin/env python3
"""
Clasificar un comic específico usando embeddings visuales.
Uso: python classify_single_comic.py <ruta_del_comic>
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


def classify_single_comic(comic_path, threshold=0.75, auto_apply=False):
    """Clasifica un comic específico."""

    # Conectar a BD
    db_path = os.path.join('data', 'babelcomics.db')
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Buscar el comic en la BD
        comic = session.query(Comicbook).filter(Comicbook.path == comic_path).first()

        if not comic:
            print(f"❌ Comic no encontrado en BD: {comic_path}")
            print(f"   Escaneá tu colección primero desde la app")
            return

        if comic.is_classified:
            print(f"ℹ️  Comic ya clasificado:")
            info = session.query(ComicbookInfo).get(int(comic.id_comicbook_info))
            if info:
                print(f"   → {info.titulo} #{info.numero}")
            return

        # Obtener cover del comic
        cover_path = comic.obtener_cover()

        if "Comic_sin_caratula" in cover_path or not os.path.exists(cover_path):
            print(f"❌ Comic sin thumbnail: {os.path.basename(comic_path)}")
            print(f"   Generá thumbnails primero desde la app")
            return

        print(f"📖 Comic: {os.path.basename(comic_path)}")
        print(f"🔍 Buscando coincidencia visual...")

        # Generar o usar embedding existente
        emb_gen = get_embedding_generator()

        if comic.embedding:
            embedding = emb_gen.json_to_embedding(comic.embedding)
            print(f"   ✓ Usando embedding existente")
        else:
            print(f"   ⏳ Generando embedding...")
            embedding = emb_gen.generate_embedding(cover_path)
            if embedding:
                comic.embedding = emb_gen.embedding_to_json(embedding)
                print(f"   ✓ Embedding generado")

        if embedding is None:
            print(f"❌ Error generando embedding")
            return

        # Cargar embeddings de covers
        covers_con_embedding = session.query(ComicbookInfoCover).filter(
            ComicbookInfoCover.embedding != None,
            ComicbookInfoCover.embedding != ''
        ).all()

        if len(covers_con_embedding) == 0:
            print("❌ No hay covers con embeddings. Ejecutá generate_cover_embeddings.py primero")
            return

        print(f"   ⏳ Comparando con {len(covers_con_embedding)} covers...")

        # Crear lista de candidatos
        cover_to_info = {cover.id_cover: cover.id_comicbook_info for cover in covers_con_embedding}
        candidatos = [
            (cover.id_cover, emb_gen.json_to_embedding(cover.embedding))
            for cover in covers_con_embedding
        ]

        # Buscar la más similar
        resultado = emb_gen.find_most_similar(embedding, candidatos)

        if resultado is None:
            print(f"❌ Sin coincidencias")
            return

        cover_id, similarity = resultado
        comicbook_info_id = cover_to_info[cover_id]

        # Obtener información del ComicbookInfo
        info = session.query(ComicbookInfo).get(comicbook_info_id)

        print(f"\n{'='*60}")
        print(f"🎯 MEJOR COINCIDENCIA:")
        print(f"{'='*60}")
        print(f"Título: {info.titulo}")
        print(f"Número: #{info.numero}")
        if info.volume:
            print(f"Serie: {info.volume.nombre}")
        print(f"Similaridad: {similarity:.2%}")
        print(f"{'='*60}\n")

        if similarity >= threshold:
            print(f"✅ Pasa el umbral de {threshold:.0%}")

            if auto_apply:
                comic.id_comicbook_info = str(comicbook_info_id)
                session.commit()
                print(f"✅ CLASIFICADO AUTOMÁTICAMENTE")
            else:
                print(f"💡 Usá --auto-apply para aplicar la clasificación")
        else:
            print(f"⚠️  No pasa el umbral de {threshold:.0%}")
            print(f"   Podés bajar el umbral con --threshold {similarity:.2f}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Clasificar un comic específico usando embeddings')
    parser.add_argument('comic_path', help='Ruta completa al archivo del comic')
    parser.add_argument('--threshold', type=float, default=0.75,
                        help='Umbral de similaridad (0.0-1.0, default: 0.75)')
    parser.add_argument('--auto-apply', action='store_true',
                        help='Aplicar clasificación automáticamente')

    args = parser.parse_args()

    classify_single_comic(args.comic_path, args.threshold, args.auto_apply)
