import re
import nltk
from difflib import SequenceMatcher

# Simple tokenizer
def simple_tokenizer(text):
    text = re.sub(r'\W+', ' ', text.lower())
    return text.split()

class PromptEvaluator:
    def __init__(self, reference_dict=None):
        self.reference_dict = reference_dict or {}

#-------------------------------------------------------------
    # Basic sanity → relevance + length
    def rule_based_eval(self, response, prompt):
        relevance = any(word in response.lower() for word in prompt.lower().split())
        sufficient_length = len(response.split()) >= 5
        return {"relevance": relevance, "length_ok": sufficient_length}
    
# ----------------------------------------------------------------------
    # Prompt adherence → is model following prompt structure
    def prompt_adherence_check(self, response, prompt):
        # if prompt asks for bullet points
        if "bullet point" in prompt.lower():
            bullet_point_count = len(re.findall(r'^\s*[-*•]', response, re.MULTILINE))
            return bullet_point_count >= 2  # Pass if ≥ 2 bullets
        
        if "numbered list" in prompt.lower() or "list in numbers" in prompt.lower():

            numbered_list_count = len(re.findall(r'^\s*\d+\.', response, re.MULTILINE))
            return numbered_list_count >=2
        
        if "concise" in prompt.lower() or "paraphrase" in prompt.lower():
            # Check that response is reasonably shorter than prompt
            original_len = len(prompt.split()) # prompt length 
            response_len = len(response.split()) # response length 
            compression_ratio = response_len / original_len

            return compression_ratio <= 0.8  # should be 20% shorter or more
        
    
#------------------------------------------------------------
    # Prompt quality → is prompt well formed
    def prompt_quality_check(self, prompt):
        words = simple_tokenizer(prompt)
        if len(words) < 5:
            return False  # Too short → bad prompt
        stopwords = set(nltk.corpus.stopwords.words('english'))
        stopword_ratio = len([w for w in words if w in stopwords]) / len(words)
        if stopword_ratio > 0.6:
            return False  # Too many stopwords → bad prompt
        return True  # Prompt looks OK

# ----------------------------------------------------------------------
    def prompt_adherence_check(self, response, prompt):
        if "bullet point" in prompt.lower():
            bullet_point_count = len(re.findall(r'^\s*[-*•]', response, re.MULTILINE))
            return bullet_point_count >= 2

        if "numbered list" in prompt.lower() or "list in numbers" in prompt.lower():
            numbered_list_count = len(re.findall(r'^\s*\d+\.', response, re.MULTILINE))
            return numbered_list_count >= 2

        if "concise" in prompt.lower() or "paraphrase" in prompt.lower():
            original_len = len(prompt.split())
            response_len = len(response.split())
            compression_ratio = response_len / original_len
            return compression_ratio <= 0.8

        if "rephrase" in prompt.lower():
            # Use SequenceMatcher to measure string similarity
            similarity = SequenceMatcher(None, prompt.lower(), response.lower()).ratio()
            return similarity < 0.8  # If it's too similar, it's not rephrased well

        return True  # Default pass
    
# ----------------------------------------------------------------------


    # Final prompt evaluation → pass/fail + all checks
    def evaluate_prompt(self, response, prompt):
        rule_check = self.rule_based_eval(response, prompt)
        adherence_check = self.prompt_adherence_check(response, prompt)
        quality_check = self.prompt_quality_check(prompt)

        # DEBUG PRINT — this helps you trace WHY Quality Check is False even when other checks look True
        print(f"\n[DEBUG] Rule Check = {rule_check}, Adherence Check = {adherence_check}, Quality Check = {quality_check}")

        flag = not all(rule_check.values()) or not adherence_check or not quality_check

        result = {
            "rule_check": rule_check,
            "adherence_check": adherence_check, 
            "quality_check": quality_check,
            "flagged": flag
        }

        if flag:
            self.log_flagged_prompt(prompt, response, result)

        return result

    def log_flagged_prompt(self, prompt, response, result):
        print("\n🚨 Prompt flagged for review:")
        print(f"Prompt: {prompt}")
        print(f"Generated Response: {response}")
        print(f"Rule Check: {result['rule_check']}")
        print(f"Adherence Check: {result['adherence_check']}")
        print(f"Quality Check: {result['quality_check']}")