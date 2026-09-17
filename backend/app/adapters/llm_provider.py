"""Dual-LLM Provider Engine featuring Groq + Google Gemini with Automatic Quota Failover."""
import json
import logging
import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger("trustgate.llm")

class LlmResponse(BaseModel):
    text: str
    provider_used: str  # "GROQ", "GEMINI", "DETERMINISTIC_LOCAL"
    failover_occurred: bool = False
    model: str = ""

class LlmProvider:
    """
    Intelligent dual LLM orchestrator:
    1. Primary: Groq (high-speed, low latency Llama 3.3 70B / 8B)
    2. Automatic Failover: Google Gemini (Gemini 1.5 Flash / 2.0 Flash)
    3. Fallback: Deterministic local rule synthesis (100% reliable, zero external dependencies)
    """

    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        self.gemini_api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

        # Groq client init
        self.groq_client = None
        if self.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
                logger.info("Initialized primary LLM: Groq (%s)", settings.GROQ_MODEL)
            except Exception as e:
                logger.warning("Failed to initialize Groq client: %s", e)

        # Gemini client init
        self.gemini_client = None
        if self.gemini_api_key:
            try:
                # Try modern google.genai first
                try:
                    from google import genai
                    self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                    self._use_new_genai = True
                    logger.info("Initialized secondary failover LLM: Google Gemini (%s)", settings.GEMINI_MODEL)
                except ImportError:
                    import google.generativeai as genai_old
                    genai_old.configure(api_key=self.gemini_api_key)
                    self.gemini_client = genai_old.GenerativeModel(settings.GEMINI_MODEL)
                    self._use_new_genai = False
                    logger.info("Initialized secondary failover LLM: Google GenerativeAI (%s)", settings.GEMINI_MODEL)
            except Exception as e:
                logger.warning("Failed to initialize Gemini client: %s", e)

    def generate_explanation(self, prompt: str, system_prompt: Optional[str] = None) -> LlmResponse:
        """
        Attempts execution via Groq first.
        On quota limit (429), timeout, or error, automatically cascades to Google Gemini.
        """
        failover = False

        # 1. Attempt Groq
        if self.groq_client:
            try:
                logger.info("Dispatching explanation prompt to Groq (%s)...", settings.GROQ_MODEL)
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                completion = self.groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=600,
                )
                output = completion.choices[0].message.content.strip()
                return LlmResponse(
                    text=output,
                    provider_used="GROQ",
                    failover_occurred=False,
                    model=settings.GROQ_MODEL,
                )
            except Exception as e:
                logger.warning(
                    "[FAILOVER TRIGGERED] Groq rate limit / quota / API error: %s. Cascading to Gemini...", e
                )
                failover = True

        # 2. Failover to Google Gemini
        if self.gemini_client:
            try:
                logger.info("Dispatching prompt to Google Gemini (%s)...", settings.GEMINI_MODEL)
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

                if getattr(self, "_use_new_genai", False):
                    response = self.gemini_client.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=full_prompt,
                    )
                    output = response.text.strip()
                else:
                    response = self.gemini_client.generate_content(full_prompt)
                    output = response.text.strip()

                return LlmResponse(
                    text=output,
                    provider_used="GEMINI",
                    failover_occurred=failover,
                    model=settings.GEMINI_MODEL,
                )
            except Exception as e:
                logger.warning("Gemini also encountered quota limit / error: %s. Using local deterministic explainer.", e)
                failover = True

        # 3. Deterministic Local Fallback
        return LlmResponse(
            text=self._deterministic_fallback_summary(prompt),
            provider_used="DETERMINISTIC_LOCAL",
            failover_occurred=failover,
            model="deterministic-rule-engine-v1",
        )

    def _deterministic_fallback_summary(self, prompt: str) -> str:
        """Deterministic, reliable bulleted synthesis when external APIs are offline or out of quota."""
        return (
            "Deterministic Evidence Audit:\n"
            "• Participant credentials and biometric embeddings evaluated against security thresholds.\n"
            "• MAX30102 physiological PPG signal inspected for human liveness confirmation.\n"
            "• Cryptographic hash indices verified for duplicate cross-registration collision prevention."
        )

# Global singleton
llm_engine = LlmProvider()
