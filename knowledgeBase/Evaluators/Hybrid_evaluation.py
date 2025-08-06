import re
import torch
from sentence_transformers import SentenceTransformer, util
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer

# Reuse your simple tokenizer:
def simple_tokenizer(text):
    text = re.sub(r'\W+', ' ', text.lower())
    return text.split()

# HybridEvaluator → uses PromptEvaluator + adds semantic / lexical scores
class HybridEvaluator:
    def __init__(self, prompt_evaluator, reference_dict=None):
        self.prompt_evaluator = prompt_evaluator  # pass PromptEvaluator instance
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.reference_dict = reference_dict or {}
        self.rouge = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True) 

    # Semantic Similarity
    def semantic_similarity(self, response, prompt):
        reference = self.reference_dict.get(prompt)
        if not reference:
            return None
        ref_embed = self.embedding_model.encode(reference, convert_to_tensor=True)
        res_embed = self.embedding_model.encode(response, convert_to_tensor=True)
        return float(util.pytorch_cos_sim(ref_embed, res_embed).item())

#---------------------------------------------------------------------------
    # BLEU Score - to check how closely generated response is to reference ( ground-truth answer) in vector store
    # by checking precision of overlapping ( words or words sequence )

    ## BLEU can return zero for short sequences (due to 0 n-gram matches).
    # So we use smoothing to avoid harsh penalties.

    def bleu_score(self, response, reference):
        smoothing = SmoothingFunction().method1
        ref_tokens = [simple_tokenizer(reference)]
        resp_tokens = simple_tokenizer(response)
        score = sentence_bleu(ref_tokens, resp_tokens, smoothing_function=smoothing)
        return score

#---------------------------------------------------------------------------
    # ROUGE Score - to check 
    def rouge_score(self, response, reference):
        scores = self.rouge.score(reference, response)
        return scores['rougeL'].fmeasure

#---------------------------------------------------------------------------

    # F1 Score - harmonic mean of precision and recall
    def f1_score(self, response, reference):
        ref_tokens = simple_tokenizer(reference)
        resp_tokens = simple_tokenizer(response)
        common = set(ref_tokens) & set(resp_tokens) ## common words btw ref and response, set intersection

        if not common:
            return 0.0 # if no common words 

        precision = len(common) / len(resp_tokens) 
        recall = len(common) / len(ref_tokens) # % of reference tokens correctly included in response

        if precision + recall == 0:
            return 0.0 

        f1 = 2 * precision * recall / (precision + recall)
        return f1


#---------------------------------------------------------------------------
    # Final Hybrid Score → combines all
    def hybrid_score(self, response, prompt, score_threshold=0.6):
        # Run PromptEvaluator first
        prompt_eval = self.prompt_evaluator.evaluate_prompt(response, prompt)

        # Run semantic + lexical scores
        semantic_score = self.semantic_similarity(response, prompt) or 0.0

        reference = self.reference_dict.get(prompt, "")
        bleu = self.bleu_score(response, reference) if reference else 0.0
        rouge = self.rouge_score(response, reference) if reference else 0.0
        f1 = self.f1_score(response, reference) if reference else 0.0




#---------------------------------------------------------------------------
        # Final Hybrid Score = avg of all scores
        final_score = (semantic_score + bleu + rouge + f1) / 4.0

        # Flag if any stage failed OR hybrid score below threshold
        flag = prompt_eval['flagged'] or final_score < score_threshold

        result = {
            "response": response,
            "semantic_score": semantic_score,
            "bleu_score": bleu,
            "rouge_score": rouge,
            "f1_score": f1,
            "hybrid_score": final_score,
            "prompt_eval": prompt_eval,
            "flagged": flag
        }

        if flag:
            self.log_flagged_result(prompt, result)

        return result

    def log_flagged_result(self, prompt, result):
        print("\n🚨 HYBRID EVAL FLAGGED 🚨")
        print(f"Prompt: {prompt}")
        print(f"Generated Response: {result['response']}")
        print("----- Prompt Evaluation -----")
        print(f"Rule Check: {result['prompt_eval']['rule_check']}")
        print(f"Adherence Check: {result['prompt_eval']['adherence_check']}")
        print(f"Quality Check: {result['prompt_eval']['quality_check']}")
        print("----- Semantic / Lexical -----")
        print(f"Semantic Score: {result['semantic_score']}")
        print(f"BLEU Score: {result['bleu_score']}")
        print(f"ROUGE Score: {result['rouge_score']}")
        print(f"F1 Score: {result['f1_score']}")
        print(f"Hybrid Score: {result['hybrid_score']}")