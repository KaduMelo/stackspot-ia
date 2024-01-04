import os
import re
import subprocess
from typing import List, Tuple

def get_review_per_file(diff: str, prompt_chunk_size: int) -> Tuple[List[str], str]:
    # Chunk the prompt
    review_prompt = get_review_prompt()
    
    # Split the diff into separate files
    file_diffs = split_diff_into_files(diff)
    
    # Get review for each file
    chunked_reviews = []
    for file_diff in file_diffs:
        if len(file_diff) > 0:
            response = get_code_review_stk_ai(review_prompt, file_diff)
            review_result = response
            chunked_reviews.append(review_result)
    
    # Summarize the chunked reviews
    summarize_prompt = get_summarize_prompt()
    summarized_review = ""
    if all(isinstance(review, str) for review in chunked_reviews):
        summarized_review = get_code_review_stk_ai(summarize_prompt, "\n".join(chunked_reviews))
    
    return chunked_reviews, summarized_review

def split_diff_into_files(diff: str) -> List[str]:
    """
    Split the diff string into a list of diffs, one for each file.
    """
    file_diffs = []
    current_file_diff = []
    for line in diff.split('\n'):
        if line.startswith('diff --git'):
            if current_file_diff:
                file_diffs.append('\n'.join(current_file_diff))
                current_file_diff = []
        current_file_diff.append(line)
    if current_file_diff:  # Add the last file diff
        file_diffs.append('\n'.join(current_file_diff))
    return file_diffs

def get_code_review_stk_ai(review_prompt: str, chunked_diff: str):
    # ... (existing implementation of get_code_review_stk_ai)
    pass

# ... (other existing functions)

if __name__ == "__main__":
    # Example usage:
    diff = os.getenv('PULL_REQUEST_DIFF')  # Get the diff from an environment variable or other source
    chunked_reviews, summarized_review = get_review_per_file(diff=diff, prompt_chunk_size=2000)
    # ... (use chunked_reviews and summarized_review as needed)
