"""Simple example showing how to call an Azure-hosted LLM with OpenHands.

This file demonstrates two patterns:

1) Using OpenHands' LLM wrapper (recommended for app usage). This keeps retries, metrics,
   and other integration behavior.

2) Calling Azure OpenAI directly with the `openai.OpenAI` client (used by some agent skills).

Security: Do NOT store API keys in this script. Use environment variables.

Env variables used:
- AZURE_OPENAI_KEY: Azure OpenAI key
- AZURE_OPENAI_ENDPOINT: https://<your-resource>.openai.azure.com
- AZURE_DEPLOYMENT_NAME: The deployment name you created in Azure

Run (PowerShell example):
  $env:AZURE_OPENAI_KEY = 'sk-...'
  $env:AZURE_OPENAI_ENDPOINT = 'https://my-resource.openai.azure.com'
  $env:AZURE_DEPLOYMENT_NAME = 'gpt-deploy-1'
  python scripts/azure_llm_example.py

"""

import os
import sys

# Detect whether pydantic is available; if not, we cannot import project LLMConfig/LLM
HAS_PYDANTIC = True
try:
    from pydantic import SecretStr
except Exception:
    HAS_PYDANTIC = False



def example_using_openhands_llm():
    """Create an LLMConfig for Azure and call LLM.completion.

    Important bits:
    - LLMConfig.model: use a string that starts with "azure/" followed by your deployment name.
      The LLM wrapper detects azure models and applies Azure-specific handling (api_version default).
    - base_url: your Azure endpoint (https://<resource>.openai.azure.com)
    - api_key: SecretStr("...") or provide via configuration loader in your app.
    """
    # If pydantic or project modules are missing, skip this example
    if not HAS_PYDANTIC:
        print('Skipping OpenHands LLM example: pydantic or project dependencies not available in this environment')
        return

    # Import project LLMConfig/LLM lazily, after we've confirmed pydantic is present
    try:
        from openhands.core.config import LLMConfig
        from openhands.llm.llm import LLM
    except Exception:
        # If running outside the project PYTHONPATH, add repo root to path and retry
        repo_root = os.path.dirname(os.path.dirname(__file__))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        try:
            from openhands.core.config import LLMConfig
            from openhands.llm.llm import LLM
        except Exception as e:
            print(f'Skipping OpenHands LLM example: cannot import project modules ({e})')
            return

    key = os.getenv('AZURE_OPENAI_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    deployment = os.getenv('AZURE_DEPLOYMENT_NAME')

    if not (key and endpoint and deployment):
        print('Skipping OpenHands LLM example: set AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_DEPLOYMENT_NAME')
        return

    # Build LLMConfig - keep defaults for other fields
    # Note: LLMConfig expects SecretStr for api_key in many code paths
    llm_config = LLMConfig(
        model=f'azure/{deployment}',
        api_key=SecretStr(key),
        base_url=endpoint,
        # api_version can be left None; LLMConfig.model_post_init will set a default for azure models
        max_output_tokens=150,
        temperature=0.0,
    )

    # Create LLM instance using the project's wrapper
    llm = LLM(config=llm_config, service_id='azure-example')

    # Send a simple chat-style prompt
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello and list 2 short tips for using Azure OpenAI."},
    ]

    resp = llm.completion(messages=messages)

    # litellm ModelResponse: extract text (choices[0].message.content)
    try:
        text = resp.choices[0].message.content
    except Exception:
        text = str(resp)

    print('\n--- OpenHands LLM Response ---')
    print(text)


# Example 2 - Use the OpenAI client directly (agent-skills style)
def example_using_openai_client():
    """Call Azure OpenAI deployment using direct REST API (requests).

    This avoids SDK-specific Azure configuration issues by issuing the
    explicit Azure REST request to the deployments chat/completions endpoint.
    """
    try:
        import requests
    except Exception:
        print('requests package not installed; skipping direct REST client example')
        return

    key = os.getenv('AZURE_OPENAI_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    deployment = os.getenv('AZURE_DEPLOYMENT_NAME')

    if not (key and endpoint and deployment):
        print('Skipping direct REST client example: set AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_DEPLOYMENT_NAME')
        return

    # Construct the Azure deployments URL. Use the 2024-12-01-preview api-version used by LLMConfig by default.
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
    url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

    headers = {
        'api-key': key,
        'Content-Type': 'application/json',
    }

    payload = {
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Say hello and list 2 short tips for using Azure OpenAI.'},
        ],
        'max_tokens': 150,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Try common response shapes
        choice = data.get('choices', [None])[0]
        if choice is None:
            text = str(data)
        else:
            # chat completions usually return a message object
            message = choice.get('message') or choice.get('text') or ''
            if isinstance(message, dict):
                text = message.get('content', '')
            else:
                text = message
    except Exception as e:
        text = f'Error calling Azure REST endpoint: {e} (url={url})'

    print('\n--- Direct REST Client Response ---')
    print(text)


if __name__ == '__main__':
    example_using_openhands_llm()
    example_using_openai_client()
