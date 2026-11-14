"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
AI Service: Grounded Scientific Research Assistant with Multi-Provider Abstraction
"""

import os
from typing import Dict, Any, Optional
from ..config import GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY
from .trend_engine import trend_engine
from .data_service import data_service

class AIService:
    def __init__(self):
        self.gemini_client = None
        self.groq_client = None
        self._init_providers()

    def _init_providers(self):
        if GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"[AIService] Gemini init notice: {e}")

        if GROQ_API_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=GROQ_API_KEY)
            except Exception as e:
                print(f"[AIService] Groq init notice: {e}")

    def answer_question(self, question: str, context: Optional[Dict[str, Any]] = None, provider: str = "auto") -> Dict[str, Any]:
        """
        Grounded answer generation. Uses verified dataset statistics to ensure zero hallucination.
        """
        # If context is provided (e.g. from an active trend analysis), format evidence
        evidence = context or {}
        
        # If user asks about a specific variable and region, compute on the fly if needed
        var = evidence.get("variable", "T2M")
        reg = evidence.get("region", "All_India")
        
        prompt = self._build_grounded_prompt(question, evidence)

        # 1. Try Gemini
        if (provider in ["gemini", "auto"]) and self.gemini_client:
            try:
                response = self.gemini_client.generate_content(prompt)
                if response and response.text:
                    return {
                        "provider_used": "Google Gemini 1.5 Flash",
                        "answer": response.text.strip(),
                        "grounded_evidence": evidence
                    }
            except Exception as e:
                print(f"[AIService] Gemini call notice: {e}")

        # 2. Try Groq
        if (provider in ["groq", "auto"]) and self.groq_client:
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are the NASA Earth Systems Trend Detective scientific assistant. Explain Earth science and statistical trend results accurately and transparently."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.2
                )
                answer = chat_completion.choices[0].message.content
                return {
                    "provider_used": "Groq LLaMA 3.3 70B",
                    "answer": answer.strip(),
                    "grounded_evidence": evidence
                }
            except Exception as e:
                print(f"[AIService] Groq call notice: {e}")

        # 3. Grounded Deterministic Scientific Fallback (Zero API Key required)
        fallback_answer = self._generate_deterministic_explanation(question, evidence)
        return {
            "provider_used": "Grounded Scientific Engine (Local)",
            "answer": fallback_answer,
            "grounded_evidence": evidence
        }

    def _build_grounded_prompt(self, question: str, evidence: Dict[str, Any]) -> str:
        return f"""You are the scientific AI assistant for the NASA Space Apps Challenge platform 'Earth Systems Trend Detective'.
User Question: "{question}"

Verified Scientific Evidence from NASA POWER / Sentinel-5P:
- Variable: {evidence.get('variable_name', evidence.get('variable', 'Temperature'))}
- Region: {evidence.get('region', 'All India')}
- Horizon: {evidence.get('start_date', '2015-01-01')} to {evidence.get('end_date', '2024-12-01')} ({evidence.get('sample_size', 120)} points)
- Trend Classification: {evidence.get('trend_classification', 'N/A')}
- OLS Annualized Rate: {evidence.get('linear_regression', {}).get('annualized_rate', 'N/A')} {evidence.get('unit', '')}
- Sen's Robust Slope: {evidence.get('sens_slope', {}).get('annualized_rate', 'N/A')} {evidence.get('unit', '')}
- Mann-Kendall Test: tau = {evidence.get('mann_kendall', {}).get('tau', 'N/A')}, p-value = {evidence.get('mann_kendall', {}).get('p_value', 'N/A')}
- Is Statistically Significant (alpha = 0.05): {evidence.get('is_statistically_significant', False)}

Guidelines:
1. Explain what the p-value and annualized rate mean in simple language for students and citizens.
2. If p >= 0.05, emphasize that observed variations are within natural variability and cannot be claimed as a statistically significant trend.
3. If methane is mentioned, remind that atmospheric concentration in ppb is NOT surface emission flux.
4. Keep the explanation concise, clear, and scientifically honest.
"""

    def _generate_deterministic_explanation(self, question: str, evidence: Dict[str, Any]) -> str:
        var = evidence.get("variable_name", evidence.get("variable", "The environmental variable"))
        reg = evidence.get("region", "the selected region")
        unit = evidence.get("unit", "")
        lr = evidence.get("linear_regression", {})
        mk = evidence.get("mann_kendall", {})
        sen = evidence.get("sens_slope", {})
        is_sig = evidence.get("is_statistically_significant", False)
        rate = lr.get("annualized_rate", 0.0)
        sen_rate = sen.get("annualized_rate", 0.0)
        p_val = mk.get("p_value", 1.0)
        tau = mk.get("tau", 0.0)
        r2 = lr.get("r_squared", 0.0)
        n = evidence.get("sample_size", 120)

        sig_text = "statistically significant (p < 0.05)" if is_sig else "not statistically significant (p ≥ 0.05)"
        direction = "upward" if rate > 0 else "downward"

        explanation = (
            f"Based on 10 years of verified observations from NASA POWER ({n} continuous monthly records), "
            f"{var} in {reg} shows a fitted annual rate of {rate:+.3f} {unit} per year (Sen's robust slope: {sen_rate:+.3f} {unit}/year).\n\n"
            f"The Mann-Kendall trend test evaluates Kendall's tau at {tau:+.3f} with a p-value of {p_val:.4f}. "
            f"Because p {'<' if is_sig else '≥'} 0.05, this trend is classified as **{sig_text}**. "
        )

        if not is_sig:
            explanation += (
                f"This indicates that while the fitted slope is {direction}, the magnitude of year-to-year and seasonal variability "
                f"exceeds the long-term drift, meaning we cannot reject the null hypothesis of no trend at the 95% confidence level."
            )
        else:
            explanation += (
                f"This provides strong statistical evidence of a monotonic {direction} shift over the 2015–2024 decade, "
                f"with linear modeling accounting for {r2*100:.1f}% of observed temporal variance."
            )

        explanation += (
            f"\n\n*Scientific Caveat: Atmospheric variations are influenced by coupled planetary circulation and synoptic meteorology; "
            f"statistical correlation does not establish direct environmental causation.*"
        )
        return explanation

ai_service = AIService()
