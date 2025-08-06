# hallucination_check.py

from sentence_transformers import SentenceTransformer, util

# Load the embedding model (once per module)
model = SentenceTransformer('all-MiniLM-L6-v2')

def hallucination_score(response: str, reference: str) -> float:
    """
    Computes a similarity score between response and reference to detect hallucination.
    A low score (e.g., < 0.6) may indicate potential hallucination.
    Returns: score (0.0 to 1.0)
    """
    if not response.strip() or not reference.strip():
        return 0.0  # Avoid division by zero or empty inputs

    response_embedding = model.encode(response, convert_to_tensor=True)
    reference_embedding = model.encode(reference, convert_to_tensor=True)

    similarity = util.pytorch_cos_sim(response_embedding, reference_embedding).item()
    return round(similarity, 3)