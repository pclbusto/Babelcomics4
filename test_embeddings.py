#!/usr/bin/env python3
"""
Script de prueba rápida para verificar que el sistema de embeddings funciona.
"""

import os
from helpers.embedding_generator import get_embedding_generator


def test_embedding_generation():
    """Prueba básica de generación de embeddings."""
    print("=" * 60)
    print("Test de Generación de Embeddings")
    print("=" * 60)

    # Inicializar generador
    print("\n1. Inicializando generador de embeddings...")
    emb_gen = get_embedding_generator()
    print("   ✓ Generador inicializado")

    # Buscar una imagen de prueba
    print("\n2. Buscando imagen de prueba...")
    test_image = None

    # Intentar encontrar una cover existente
    covers_dir = "data/thumbnails/comicbook_info"
    if os.path.exists(covers_dir):
        for root, dirs, files in os.walk(covers_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.png', '.jpeg')):
                    test_image = os.path.join(root, file)
                    break
            if test_image:
                break

    if not test_image:
        # Intentar con thumbnails de comics
        comics_dir = "data/thumbnails/comics"
        if os.path.exists(comics_dir):
            for file in os.listdir(comics_dir):
                if file.lower().endswith(('.jpg', '.png', '.jpeg')):
                    test_image = os.path.join(comics_dir, file)
                    break

    if not test_image:
        print("   ⊗ No se encontró ninguna imagen de prueba")
        print("   Tip: Descarga algunas covers primero")
        return False

    print(f"   ✓ Imagen encontrada: {test_image}")

    # Generar embedding
    print("\n3. Generando embedding...")
    embedding = emb_gen.generate_embedding(test_image)

    if embedding is None:
        print("   ⊗ Error generando embedding")
        return False

    print(f"   ✓ Embedding generado ({len(embedding)} dimensiones)")
    print(f"   Primeros valores: {embedding[:5]}")

    # Convertir a JSON y de vuelta
    print("\n4. Probando conversión JSON...")
    json_str = emb_gen.embedding_to_json(embedding)
    print(f"   ✓ JSON generado ({len(json_str)} caracteres)")

    recovered = emb_gen.json_to_embedding(json_str)
    print(f"   ✓ Embedding recuperado ({len(recovered)} dimensiones)")

    # Calcular similaridad consigo mismo (debe ser ~1.0)
    print("\n5. Probando cálculo de similaridad...")
    similarity = emb_gen.calculate_similarity(embedding, embedding)
    print(f"   ✓ Similaridad consigo mismo: {similarity:.4f}")

    if abs(similarity - 1.0) > 0.01:
        print("   ⊗ ERROR: La similaridad consigo mismo debería ser ~1.0")
        return False

    print("\n" + "=" * 60)
    print("✅ TODAS LAS PRUEBAS PASARON")
    print("=" * 60)
    print("\nPróximos pasos:")
    print("1. Ejecuta: python3 generate_cover_embeddings.py")
    print("   (Genera embeddings de todas las covers de ComicbookInfo)")
    print()
    print("2. Ejecuta: python3 auto_classify_comics.py")
    print("   (Clasifica automáticamente comics sin clasificar)")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_embedding_generation()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n⊗ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
