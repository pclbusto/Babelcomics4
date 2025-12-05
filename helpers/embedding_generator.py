"""
Generador de embeddings de imágenes usando CLIP.
Permite comparar similaridad visual entre covers de comics.
"""

import json
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel


class EmbeddingGenerator:
    """Genera embeddings de imágenes usando el modelo CLIP de OpenAI."""

    _instance = None
    _model = None
    _processor = None

    def __new__(cls):
        """Singleton para no cargar el modelo múltiples veces."""
        if cls._instance is None:
            cls._instance = super(EmbeddingGenerator, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa el modelo CLIP si no está cargado."""
        if self._model is None:
            print("Cargando modelo CLIP...")
            # Usar modelo pequeño para velocidad
            model_name = "openai/clip-vit-base-patch32"
            self._model = CLIPModel.from_pretrained(model_name)
            self._processor = CLIPProcessor.from_pretrained(model_name)

            # Usar GPU si está disponible, sino CPU
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model.to(self.device)
            self._model.eval()

            if self.device == "cuda":
                gpu_name = torch.cuda.get_device_name(0)
                print(f"Modelo CLIP cargado en GPU: {gpu_name}")
            else:
                print(f"Modelo CLIP cargado en CPU")

    def generate_embedding(self, image_path):
        """
        Genera un embedding vectorial para una imagen.

        Args:
            image_path: Ruta a la imagen

        Returns:
            Lista de floats representando el embedding (512 dimensiones)
            None si hay error
        """
        try:
            # Cargar y procesar imagen
            image = Image.open(image_path).convert("RGB")

            # Procesar con CLIP
            inputs = self._processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generar embedding
            with torch.no_grad():
                image_features = self._model.get_image_features(**inputs)

            # Normalizar el embedding (importante para cosine similarity)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Convertir a lista de Python
            embedding = image_features.cpu().numpy()[0].tolist()

            return embedding

        except Exception as e:
            print(f"Error generando embedding para {image_path}: {e}")
            return None

    def embedding_to_json(self, embedding):
        """Convierte un embedding a string JSON para guardar en DB."""
        if embedding is None:
            return None
        return json.dumps(embedding)

    def json_to_embedding(self, json_str):
        """Convierte un string JSON a numpy array."""
        if not json_str:
            return None
        return np.array(json.loads(json_str))

    def calculate_similarity(self, embedding1, embedding2):
        """
        Calcula similaridad coseno entre dos embeddings.

        Args:
            embedding1, embedding2: Pueden ser listas, numpy arrays o JSON strings

        Returns:
            Float entre 0 y 1 (1 = idénticos, 0 = completamente diferentes)
        """
        # Convertir a numpy arrays si es necesario
        if isinstance(embedding1, str):
            embedding1 = self.json_to_embedding(embedding1)
        if isinstance(embedding2, str):
            embedding2 = self.json_to_embedding(embedding2)

        if embedding1 is None or embedding2 is None:
            return 0.0

        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)

        # Cosine similarity (ya están normalizados, así que es solo el producto punto)
        similarity = np.dot(emb1, emb2)

        return float(similarity)

    def find_most_similar(self, query_embedding, candidate_embeddings):
        """
        Encuentra el embedding más similar de una lista de candidatos.

        Args:
            query_embedding: Embedding a buscar (lista, array o JSON)
            candidate_embeddings: Lista de tuplas (id, embedding)

        Returns:
            Tupla (id, similarity_score) del más similar
            None si no hay candidatos
        """
        if not candidate_embeddings:
            return None

        # Convertir query a numpy
        if isinstance(query_embedding, str):
            query_embedding = self.json_to_embedding(query_embedding)

        if query_embedding is None:
            return None

        query = np.array(query_embedding)

        best_match = None
        best_similarity = -1

        for candidate_id, candidate_emb in candidate_embeddings:
            similarity = self.calculate_similarity(query, candidate_emb)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = (candidate_id, similarity)

        return best_match


# Instancia global
_embedding_generator = None

def get_embedding_generator():
    """Obtiene la instancia singleton del generador de embeddings."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator
