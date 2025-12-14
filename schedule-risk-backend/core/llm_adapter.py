"""
LLM adapter for natural language explanations
Supports multiple providers in priority order:
1. Hugging Face (preferred, using huggingface_hub library)
2. Groq (fast API, free tier)
"""

from typing import Dict, List, Optional
import httpx
import os

# Try to import huggingface_hub for better API support
try:
    from huggingface_hub import InferenceClient
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    InferenceClient = None


def explain_rule_based(activity, features: Dict, risk_score: float) -> Dict:
    """Generate rule-based explanation for risk score"""
    reasons = []
    suggestions = []
    
    if features.get("delay_baseline_days", 0) > 0:
        reasons.append(f"It is delayed by {features['delay_baseline_days']:.1f} days compared to baseline.")
        suggestions.append("Review and update the schedule to reflect current status.")
    
    if features.get("is_on_critical_path", False):
        reasons.append("It is on the critical path, meaning any delay will directly impact project completion.")
        suggestions.append("Prioritize resources and attention to this activity.")
    
    if features.get("progress_slip", 0) > 0.2:
        reasons.append(f"Work progress is {features['progress_slip']*100:.1f}% behind schedule.")
        suggestions.append("Investigate causes of delay and consider adding resources.")
    
    if features.get("expected_delay_days", 0) > 5:
        reasons.append(f"Expected delay risk is {features['expected_delay_days']:.1f} days based on probability and impact.")
        suggestions.append("Implement risk mitigation strategies to reduce probability or impact.")
    
    if features.get("float_days", 999) <= 2:
        reasons.append(f"Very low float ({features['float_days']:.1f} days), leaving little room for delays.")
        suggestions.append("Monitor closely and have contingency plans ready.")
    
    if features.get("successor_count", 0) >= 3:
        reasons.append(f"Has {features['successor_count']} successor activities, so delays will cascade.")
        suggestions.append("Ensure this activity completes on time to avoid blocking multiple downstream tasks.")
    
    if not reasons:
        reasons.append("Activity has moderate risk factors.")
        suggestions.append("Continue monitoring and maintain current schedule.")
    
    return {
        "risk_score": risk_score,
        "reasons": reasons,
        "suggestions": suggestions,
        "method": "rule_based"
    }


async def explain_with_groq(prompt: str, api_key: str, model: str = "llama-3.1-8b-instant") -> Optional[str]:
    """Try Groq (fast, free tier available)"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.7
                }
            )
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
    return None


async def explain_with_llm(activity, features: Dict, risk_score: float, 
                           criticality_index: Optional[float] = None,
                           anomalies: Optional[List[str]] = None,
                           mitigation_options: Optional[List[Dict]] = None) -> Dict:
    """
    Generate explanation using available LLM providers with structured prompt.
    Priority: Hugging Face (preferred) -> Groq -> Ollama
    
    Uses structured JSON-like payload as per specification.
    """
    
    # Build structured payload (as per spec)
    structured_data = {
        "activity_id": activity.activity_id,
        "activity_name": activity.name,
        "risk_score": round(risk_score, 1),
        "criticality_index": round(criticality_index, 2) if criticality_index is not None else None,
        "anomalies": anomalies or [],
        "delay_days": round(features.get('delay_baseline_days', 0), 1),
        "float_days": round(features.get('float_days', 0), 1),
        "on_critical_path": features.get('is_on_critical_path', False),
        "progress_slip": round(features.get('progress_slip', 0) * 100, 1),
        "expected_delay_days": round(features.get('expected_delay_days', 0), 1),
        "predecessor_count": features.get('predecessor_count', 0),
        "successor_count": features.get('successor_count', 0),
        "downstream_critical_depth": features.get('downstream_critical_depth', 0),
        "resource_utilization": round(features.get('resource_utilization', 0) * 100, 1),
        "risk_probability": round(features.get('risk_probability', 0) * 100, 1),
        "risk_delay_impact_days": round(features.get('risk_delay_impact_days', 0), 1),
        "cost_impact_of_risk": features.get('cost_impact_of_risk', 0),
        "mitigation_options": mitigation_options or []
    }
    
    # Build natural language prompt from structured data
    prompt = f"""You are a project risk analysis expert. Explain why activity "{activity.name}" (ID: {activity.activity_id}) has a risk score of {risk_score:.1f}/100.

Activity Details:
- Risk Score: {risk_score:.1f}/100
- Criticality Index: {criticality_index:.2f} (if available)
- Delay from baseline: {structured_data['delay_days']} days
- On critical path: {structured_data['on_critical_path']}
- Total float: {structured_data['float_days']} days
- Progress slip: {structured_data['progress_slip']}%
- Expected delay: {structured_data['expected_delay_days']} days
- Predecessors: {structured_data['predecessor_count']}
- Successors: {structured_data['successor_count']}
- Downstream critical depth: {structured_data['downstream_critical_depth']}
- Resource utilization: {structured_data['resource_utilization']}%
- Risk probability: {structured_data['risk_probability']}%
- Risk delay impact: {structured_data['risk_delay_impact_days']} days
- Cost impact: {structured_data['cost_impact_of_risk']}

Anomalies detected: {', '.join(anomalies) if anomalies else 'None'}

Provide:
1. A clear explanation of why this activity is at risk
2. What's driving the risk (delay, bottlenecks, dependencies, etc.)
3. 2-3 actionable mitigation recommendations

Format your response clearly with sections for Explanation, Risk Drivers, and Recommendations."""

    # Try providers in order: Hugging Face (preferred) -> Groq
    providers_tried = []
    explanation = None
    last_error = None
    
    # 1. Try Hugging Face first (using huggingface_hub library - tested and working)
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    hf_model = os.getenv("HUGGINGFACE_MODEL", "Qwen/Qwen2.5-7B-Instruct:together")
    
    if hf_api_key and HF_HUB_AVAILABLE:
        try:
            providers_tried.append(f"Hugging Face ({hf_model})")
            client = InferenceClient(api_key=hf_api_key)
            completion = client.chat.completions.create(
                model=hf_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,  # Increased for complete responses
                temperature=0.7
            )
            explanation = completion.choices[0].message.content.strip()
            
            if explanation:
                # Extract suggestions if present in the explanation
                suggestions = []
                if "### Action" in explanation or "### Suggestions" in explanation or "Actionable" in explanation:
                    # Try to extract suggestions from the explanation
                    parts = explanation.split("### Action")
                    if len(parts) > 1:
                        action_part = parts[1].strip()
                        # Extract numbered or bulleted suggestions
                        import re
                        suggestion_matches = re.findall(r'(?:^|\n)\s*(?:[-•*]|\d+\.)\s*(.+?)(?=\n|$)', action_part, re.MULTILINE)
                        if suggestion_matches:
                            suggestions = [s.strip() for s in suggestion_matches[:3]]  # Limit to 3
                
                # If no suggestions extracted, use default
                if not suggestions:
                    suggestions = ["Review the explanation above for specific recommendations."]
                
                # Clean up markdown for better display (optional - can keep markdown if frontend supports it)
                # For now, keep the explanation as-is since it contains useful formatting
                
                # Parse explanation into structured format (robust parsing)
                import re
                reasons = []
                recommendations = []
                
                # Try multiple patterns to extract explanation/reasons
                explanation_lower = explanation.lower()
                
                # Pattern 1: Markdown headers (### Explanation, ## Explanation, etc.)
                if "### explanation" in explanation_lower or "## explanation" in explanation_lower:
                    # Find explanation section
                    pattern = r'(?:^|\n)\s*#{1,3}\s*[Ee]xplanation[:\s]*(.+?)(?=\n\s*#{1,3}|$)'
                    matches = re.findall(pattern, explanation, re.DOTALL | re.MULTILINE)
                    if matches:
                        explanation_text = matches[0].strip()
                        # Remove next section headers if present
                        explanation_text = re.split(r'\n\s*#{1,3}\s*(?:Risk|Recommendation|Action)', explanation_text)[0].strip()
                        if explanation_text:
                            reasons.append(explanation_text)
                
                # Pattern 2: Plain text "Explanation:" or "Why:"
                if not reasons:
                    for pattern in [r'[Ee]xplanation[:\s]+(.+?)(?=\n\s*(?:Risk|Recommendation|Action|$))', 
                                   r'[Ww]hy[:\s]+(.+?)(?=\n\s*(?:Risk|Recommendation|Action|$))']:
                        matches = re.findall(pattern, explanation, re.DOTALL | re.MULTILINE)
                        if matches:
                            explanation_text = matches[0].strip()
                            if explanation_text and len(explanation_text) > 20:  # Minimum length
                                reasons.append(explanation_text)
                                break
                
                # Extract recommendations - try multiple patterns
                # Pattern 1: Markdown headers
                if "### recommendation" in explanation_lower or "## recommendation" in explanation_lower:
                    pattern = r'(?:^|\n)\s*#{1,3}\s*[Rr]ecommendation[s]?[:\s]*(.+?)(?=\n\s*#{1,3}|$)'
                    matches = re.findall(pattern, explanation, re.DOTALL | re.MULTILINE)
                    if matches:
                        rec_text = matches[0]
                        # Extract bullet points or numbered items
                        rec_matches = re.findall(r'(?:^|\n)\s*(?:[-•*]|\d+\.)\s*(.+?)(?=\n|$)', rec_text, re.MULTILINE)
                        recommendations = [r.strip() for r in rec_matches[:3] if r.strip()]
                
                # Pattern 2: Plain text "Recommendations:" or "Actions:"
                if not recommendations:
                    for pattern in [r'[Rr]ecommendation[s]?[:\s]+(.+?)(?=\n\s*(?:Explanation|Why|$))',
                                   r'[Aa]ction[s]?[:\s]+(.+?)(?=\n\s*(?:Explanation|Why|$))']:
                        matches = re.findall(pattern, explanation, re.DOTALL | re.MULTILINE)
                        if matches:
                            rec_text = matches[0]
                            rec_matches = re.findall(r'(?:^|\n)\s*(?:[-•*]|\d+\.)\s*(.+?)(?=\n|$)', rec_text, re.MULTILINE)
                            recommendations = [r.strip() for r in rec_matches[:3] if r.strip()]
                            if recommendations:
                                break
                
                # Pattern 3: Look for numbered or bulleted items anywhere in explanation
                if not recommendations:
                    # Look for common recommendation patterns
                    rec_matches = re.findall(r'(?:^|\n)\s*(?:[-•*]|\d+\.)\s*(.+?)(?=\n|$)', explanation, re.MULTILINE)
                    # Filter for actionable items (contain verbs like "add", "reduce", "implement", etc.)
                    action_verbs = ['add', 'reduce', 'implement', 'review', 'consider', 'ensure', 'prioritize', 'monitor']
                    filtered_recs = [r.strip() for r in rec_matches if any(verb in r.lower() for verb in action_verbs)]
                    if filtered_recs:
                        recommendations = filtered_recs[:3]
                    elif rec_matches:
                        # Fallback: use any bullet points
                        recommendations = [r.strip() for r in rec_matches[:3] if r.strip()]
                
                # If parsing failed, use intelligent fallback
                if not reasons:
                    # Use first paragraph or first 200 characters as reason
                    first_para = explanation.split('\n\n')[0] if '\n\n' in explanation else explanation[:200]
                    if first_para.strip():
                        reasons.append(first_para.strip())
                    else:
                        reasons.append(explanation[:300])  # Last resort
                
                if not recommendations:
                    # Try to extract any actionable sentences
                    sentences = re.split(r'[.!?]\s+', explanation)
                    action_sentences = [s.strip() for s in sentences if any(verb in s.lower() for verb in ['should', 'recommend', 'suggest', 'consider', 'implement'])]
                    if action_sentences:
                        recommendations = action_sentences[:3]
                    else:
                        recommendations = ["Review the explanation above for specific recommendations."]
                
                return {
                    "risk_score": risk_score,
                    "explanation": explanation,
                    "reasons": reasons,
                    "suggestions": recommendations,
                    "method": "llm_huggingface",
                    "model_used": hf_model,
                    "structured_data": structured_data  # Include structured payload
                }
        except Exception as e:
            error_str = str(e)
            # Check if it's a model not supported error
            if "model_not_supported" in error_str or "not supported" in error_str.lower():
                last_error = f"Hugging Face error: Model '{hf_model}' is not supported. Try 'Qwen/Qwen2.5-7B-Instruct:together' instead. Error: {error_str}"
            else:
                last_error = f"Hugging Face error: {error_str}"
    
    # 2. Try Groq (fast, free tier available)
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key and not explanation:
        groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        providers_tried.append(f"Groq ({groq_model})")
        explanation = await explain_with_groq(prompt, groq_api_key, groq_model)
        if explanation:
            return {
                "risk_score": risk_score,
                "explanation": explanation,
                "reasons": [explanation],
                "suggestions": ["Review the explanation above for specific recommendations."],
                "method": "llm_groq",
                "model_used": groq_model
            }
    
    # If we get here, all providers failed
    result = explain_rule_based(activity, features, risk_score)
    result["llm_error"] = f"All LLM providers failed. Tried: {', '.join(providers_tried)}. Last error: {last_error or 'No providers configured'}"
    result["llm_debug"] = {
        "providers_tried": providers_tried,
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "huggingface_configured": bool(os.getenv("HUGGINGFACE_API_KEY")),
        "last_error": last_error,
        "setup_instructions": {
            "groq": "1. Get free API key at https://console.groq.com 2. Set GROQ_API_KEY environment variable",
            "huggingface": "1. Get API key at https://huggingface.co/settings/tokens 2. Set HUGGINGFACE_API_KEY"
        }
    }
    return result


def explain(activity, features: Dict, risk_score: float, use_llm: bool = False) -> Dict:
    """Generate explanation for risk score (synchronous wrapper)"""
    if use_llm:
        # For async LLM, we'll need to handle it in the API endpoint
        return explain_rule_based(activity, features, risk_score)
    else:
        return explain_rule_based(activity, features, risk_score)

