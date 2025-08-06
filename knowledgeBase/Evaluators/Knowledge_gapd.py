# knowledgeGapD.py

from sentence_transformers import SentenceTransformer, util

# Load embedding model once globally for efficiency
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def knowledge_gap_detection(response: str, reference_answer: str):
    """
    Detects knowledge gap by computing semantic similarity between
    the generated response and the ground truth answer.
    
    Returns:
        (bool, float): Pass/Fail flag and similarity score
    """
    response_embedding = embedding_model.encode(response, convert_to_tensor=True)
    reference_embedding = embedding_model.encode(reference_answer, convert_to_tensor=True)
    
    similarity = util.pytorch_cos_sim(response_embedding, reference_embedding).item()
    return similarity >= 0.8, similarity  # threshold can be adjusted


def embedding_similarity_check(generated_response: str, retrieved_context: str):
    """
    Measures how well the generated response aligns with the retrieved context.

    Returns:
        float: cosine similarity score (0.0 to 1.0)
    """
    gen_embedding = embedding_model.encode(generated_response, convert_to_tensor=True)
    ctx_embedding = embedding_model.encode(retrieved_context, convert_to_tensor=True)

    return util.pytorch_cos_sim(gen_embedding, ctx_embedding).item()