from transformers import pipeline

# Load zero-shot toxicity classifier (will auto-download model on first run)
classifier = pipeline("text-classification", model="unitary/toxic-bert", top_k=None)

def check_toxicity(text):
    """
    Returns:
        flagged (bool): True if text is toxic
        score (float): Toxicity score (0.0 - 1.0)
    """
    result = classifier(text)[0]
    toxic_score = 0.0

    for label in result:
        if label["label"] == "toxic":
            toxic_score = label["score"]
            break

    # Flag if toxic score is above threshold
    return toxic_score > 0.5, round(toxic_score, 3)