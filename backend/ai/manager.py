import os

from dotenv import load_dotenv

from backend.ai.fallback_provider import understand_with_fallback
from backend.ai.gemini_provider import understand_with_gemini
from backend.ai.ollama_provider import understand_with_ollama
from backend.ai.openrouter_provider import understand_with_openrouter


load_dotenv()


def understand_workflow(candidate: dict) -> dict:
    """
    WorkFlowOS AI provider manager.

    Provider priority:

    1. OpenRouter
       - Primary cloud AI provider
       - Can route across multiple models/providers

    2. Gemini
       - Secondary cloud AI provider

    3. Deterministic fallback
       - Guaranteed to work without an external AI service

    4. Ollama
       - Optional local AI provider
       - Used only as a final AI fallback so it cannot
         block the normal demo flow.
    """

    # =========================================================
    # 1. OPENROUTER — PRIMARY AI PROVIDER
    # =========================================================

    if os.getenv("OPENROUTER_API_KEY"):
        try:
            print("[AI] Trying OpenRouter...")

            result = understand_with_openrouter(candidate)

            print("[AI] OpenRouter succeeded.")

            return {
                "success": True,
                "provider": "openrouter",
                "mode": "cloud_ai",
                "workflow": result.model_dump(),
            }

        except Exception as error:
            print(f"[AI] OpenRouter failed: {error}")

    else:
        print("[AI] OpenRouter API key not configured.")

    # =========================================================
    # 2. GEMINI — SECONDARY CLOUD PROVIDER
    # =========================================================

    if os.getenv("GEMINI_API_KEY"):
        try:
            print("[AI] Trying Gemini...")

            result = understand_with_gemini(candidate)

            print("[AI] Gemini succeeded.")

            return {
                "success": True,
                "provider": "gemini",
                "mode": "cloud_ai",
                "workflow": result.model_dump(),
            }

        except Exception as error:
            print(f"[AI] Gemini failed: {error}")

    else:
        print("[AI] Gemini API key not configured.")

    # =========================================================
    # 3. DETERMINISTIC FALLBACK
    # =========================================================
    #
    # This is intentionally before Ollama.
    #
    # The deterministic provider is fast and guaranteed to
    # produce a valid WorkFlowOS workflow structure.
    #
    # We don't want a slow local LLM to block the prototype.
    # =========================================================

    try:
        print("[AI] Using deterministic fallback...")

        result = understand_with_fallback(candidate)

        print("[AI] Deterministic fallback succeeded.")

        return {
            "success": True,
            "provider": "deterministic",
            "mode": "fallback",
            "workflow": result.model_dump(),
        }

    except Exception as error:
        print(f"[AI] Deterministic fallback failed: {error}")

    # =========================================================
    # 4. OLLAMA — FINAL LOCAL AI FALLBACK
    # =========================================================
    #
    # Ollama remains part of the architecture, but it is placed
    # last because local inference on this machine was slow.
    #
    # This means Ollama can still be used if the other providers
    # and deterministic processing fail.
    # =========================================================

    try:
        print("[AI] Trying Ollama as final fallback...")

        result = understand_with_ollama(candidate)

        print("[AI] Ollama succeeded.")

        return {
            "success": True,
            "provider": "ollama",
            "mode": "local_ai",
            "workflow": result.model_dump(),
        }

    except Exception as error:
        print(f"[AI] Ollama failed: {error}")

    # =========================================================
    # EVERYTHING FAILED
    # =========================================================

    return {
        "success": False,
        "provider": "none",
        "mode": "error",
        "error": "All AI providers failed.",
    }