import json
import os
from typing import List
import pexpect
import re
import click
import requests
from loguru import logger
import subprocess



def check_required_env_vars():
    """Check required environment variables"""
    required_env_vars = [
        "GITHUB_TOKEN",
        "GITHUB_REPOSITORY",
        "GITHUB_PULL_REQUEST_NUMBER",
        "GIT_COMMIT_HASH",
    ]
    for required_env_var in required_env_vars:
        if os.getenv(required_env_var) is None:
            raise ValueError(f"{required_env_var} is not set")


def get_review_prompt() -> str:
    template = f"""
    Esta é uma solicitação pull ou parte de uma solicitação pull se a solicitação pull for muito grande.
    Suponha que você analise este PR como um excelente engenheiro de software e um excelente engenheiro de segurança.
    Você pode me contar os problemas com diferenças em uma solicitação pull e fornecer sugestões para melhorá-la?
    Você pode fornecer um resumo da revisão e comentários sobre os problemas por arquivo, se algum problema importante for encontrado.
    Comece a resposta com INICIO ao contrario e encerre a resposta com a palavra FINAL ao contrario, mesmo se não for informado codigo.
    """
    return template


def get_summarize_prompt() -> str:
    template = """
    Esta é uma solicitação pull de um conjunto de revisões de uma solicitação pull.
    Eles são gerados por uma inteligência artificial generativa.
    Você pode resumi-los?
    Seria bom focar em destacar problemas e fornecer sugestões para melhorar a solicitação pull.
    Comece a resposta com INICIO ao contrario e encerre a resposta com a palavra FINAL ao contrario, mesmo se não for informado codigo.
    """
    return template


def create_a_comment_to_pull_request(
        github_token: str,
        github_repository: str,
        pull_request_number: int,
        git_commit_hash: str,
        body: str):
    headers = {
        "Accept": "application/vnd.github.v3.patch",
        "authorization": f"Bearer {github_token}"
    }
    data = {
        "body": body,
        "commit_id": git_commit_hash,
        "event": "COMMENT"
    }
    url = f"https://api.github.com/repos/{github_repository}/pulls/{pull_request_number}/reviews"
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response


def chunk_string(input_string: str, chunk_size) -> List[str]:
    """Chunk a string"""
    chunked_inputs = []
    for i in range(0, len(input_string), chunk_size):
        chunked_inputs.append(input_string[i:i + chunk_size])
    return chunked_inputs


def get_review(
        diff: str,
        prompt_chunk_size: int
):
    # Chunk the prompt
    review_prompt = get_review_prompt()
    chunked_diff_list = chunk_string(input_string=diff, chunk_size=prompt_chunk_size)
    # Get summary by chunk
    chunked_reviews = []
    for chunked_diff in chunked_diff_list:
        if  len(chunked_diff) > 0:
            response = get_code_review_stk_ai(review_prompt, chunked_diff)
            review_result = response
            chunked_reviews.append(review_result)
    # If the chunked reviews are only one, return it
    if len(chunked_reviews) == 1:
        return chunked_reviews, chunked_reviews[0]

    # Summarize the chunked reviews
    summarize_prompt = get_summarize_prompt()

    summarized_review = ""
    if all(isinstance(review, str) for review in chunked_reviews):
        summarized_review = get_code_review_stk_ai(summarize_prompt, "\n".join(chunked_reviews))

    return chunked_reviews, summarized_review


def format_review_comment(summarized_review: str, chunked_reviews: List[str]) -> str:
    """Format reviews"""
    if len(chunked_reviews) == 1:
        return summarized_review
    unioned_reviews = ""
    if all(isinstance(review, str) for review in chunked_reviews):
        unioned_reviews = "\n".join(chunked_reviews)
    review = f"""<details>
    <summary>{summarized_review}</summary>
    {unioned_reviews}
    </details>
    """
    return review


@click.command()
@click.option("--diff-chunk-size", type=click.INT, required=False, default=2000, help="Pull request diff")
def main(
        diff_chunk_size: int
):
    # Set log level
    # Check if necessary environment variables are set or not
    check_required_env_vars()

    # Request a code review
    chunked_reviews, summarized_review = get_review(
        diff=os.getenv('PULL_REQUEST_DIFF'),
        prompt_chunk_size=diff_chunk_size
    )
    
  

    # Format reviews
    review_comment = format_review_comment(summarized_review=summarized_review,
                                           chunked_reviews=chunked_reviews)
    # Create a comment to a pull request
    create_a_comment_to_pull_request(
        github_token=os.getenv("GITHUB_TOKEN"),
        github_repository=os.getenv("GITHUB_REPOSITORY"),
        pull_request_number=int(os.getenv("GITHUB_PULL_REQUEST_NUMBER")),
        git_commit_hash=os.getenv("GIT_COMMIT_HASH"),
        body=review_comment
    )

def get_code_review_stk_ai(review_prompt: str, chunked_diff: str):
    mesage = review_prompt + '\n' + chunked_diff
    process = subprocess.Popen(["expect", 'script.sh', mesage], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()
    print("Saída do programa:", output)
    print("Erro do programa:", error)

    regex = re.compile(r'OICNI(.*?)(INALF|$)', re.DOTALL)
    response =  regex.search(output)

    return response.group(1)

if __name__ == "__main__":
    main()

def sum(a: int, b: int):
    return a + b

def concat(a: str, b: str):
    return a + b