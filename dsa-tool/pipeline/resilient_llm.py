"""
GritX — Resilient LLM Streaming, Continuation & JSON Repair Engine
Handles streaming cut-offs, token truncations, gateway timeouts, and broken JSON.
"""
import re
import json
import time
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from openai import OpenAI
import httpx
from json_repair import repair_json

from config import (
    LLM_BASE_URL,
    LLM_STANDARD_API_KEY,
    LLM_STANDARD_MODEL,
    LLM_NON_STREAMING_TIMEOUT,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_MAX_TOKENS,
)

logger = logging.getLogger(__name__)


def clean_json_fences(text: str) -> str:
    """Strips markdown code fences and extraneous leading/trailing whitespace."""
    s = text.strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def is_json_incomplete(text: str) -> Tuple[bool, str]:
    """
    Deterministically detects whether a JSON string was cut off mid-generation.
    Returns (is_incomplete: bool, reason: str).
    """
    clean = clean_json_fences(text)
    if not clean:
        return True, "Empty text"
    
    # Check 1: Does not end with expected root closing brace
    if not clean.endswith("}") and not clean.endswith("]"):
        return True, "Does not end with closing brace '}' or ']'"
    
    # Check 2: Unbalanced braces
    open_curly = clean.count("{")
    close_curly = clean.count("}")
    if open_curly != close_curly:
        return True, f"Unbalanced curly braces: {open_curly} open vs {close_curly} closed"
        
    open_sq = clean.count("[")
    close_sq = clean.count("]")
    if open_sq != close_sq:
        return True, f"Unbalanced square brackets: {open_sq} open vs {close_sq} closed"
        
    # Check 3: Odd number of unescaped quotes (indicates cut-off mid-string)
    unescaped_quotes = sum(1 for _ in re.finditer(r'(?<!\\)"', clean))
    if unescaped_quotes % 2 != 0:
        return True, f"Odd number of unescaped quotes ({unescaped_quotes})"

    # Check 4: Standard parse test
    try:
        json.loads(clean)
        return False, "Complete valid JSON"
    except json.JSONDecodeError as err:
        return True, f"JSONDecodeError: {err.msg} at line {err.lineno} col {err.colno}"


def salvage_completed_elements(text: str, list_key: str = "problems_discussed") -> List[Dict[str, Any]]:
    """
    If a JSON document was truncated mid-list, parses and extracts all fully-formed
    dict elements in the target array before the truncation point.
    """
    clean = clean_json_fences(text)
    items = []
    
    # Locate target array start
    idx = clean.find(f'"{list_key}"')
    if idx == -1:
        return items
        
    bracket_idx = clean.find('[', idx)
    if bracket_idx == -1:
        return items
        
    sub = clean[bracket_idx + 1:]
    
    # Scan for balanced top-level { } objects within the array
    depth = 0
    start_pos = -1
    in_str = False
    escape = False
    
    for i, ch in enumerate(sub):
        if ch == '"' and not escape:
            in_str = not in_str
        elif ch == '\\' and not escape:
            escape = True
            continue
        elif not in_str:
            if ch == '{':
                if depth == 0:
                    start_pos = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start_pos != -1:
                    candidate = sub[start_pos:i+1]
                    try:
                        obj = json.loads(candidate)
                        items.append(obj)
                    except Exception:
                        try:
                            obj = json.loads(repair_json(candidate))
                            items.append(obj)
                        except Exception:
                            pass
                    start_pos = -1
        escape = False
        
    return items


def resilient_json_parse(text: str, default: Any = None, fallback_list_key: Optional[str] = None) -> Any:
    """
    Multi-stage resilient JSON parser:
    1. Direct json.loads()
    2. Deterministic AST repair via json_repair
    3. Structural element salvage if partial array
    """
    clean = clean_json_fences(text)
    
    # Stage 1: Native parse
    try:
        return json.loads(clean)
    except json.JSONDecodeError as native_err:
        logger.warning(f"Standard JSON decode failed: {native_err}. Attempting json_repair...")
        
    # Stage 2: json_repair AST reconstruction
    try:
        repaired = repair_json(clean)
        parsed = json.loads(repaired)
        if parsed and (isinstance(parsed, dict) or isinstance(parsed, list)):
            logger.info("Successfully repaired truncated/malformed JSON via json_repair.")
            return parsed
    except Exception as repair_err:
        logger.warning(f"json_repair failed: {repair_err}. Attempting structural element salvage...")

    # Stage 3: Structural element salvage
    if fallback_list_key:
        salvaged = salvage_completed_elements(clean, list_key=fallback_list_key)
        if salvaged:
            logger.info(f"Salvaged {len(salvaged)} fully-formed elements for key '{fallback_list_key}'.")
            return {fallback_list_key: salvaged}
            
    if default is not None:
        return default
        
    raise ValueError(f"Could not parse or repair JSON. Payload preview: {clean[:200]}...")


def request_tail_continuation(
    client: OpenAI,
    model: str,
    truncated_buffer: str,
    timeout: float = 90.0,
    temperature: float = 0.2
) -> str:
    """
    Sends the tail of the accumulated stream buffer back to the SAME LLM,
    asking it to pick up exactly from the truncation point and finish the JSON.
    Uses ~1,000 tokens instead of the 30,000 token transcript!
    """
    clean_buf = clean_json_fences(truncated_buffer)
    # Take the last 1500 characters of the accumulated buffer
    tail_context = clean_buf[-1500:] if len(clean_buf) > 1500 else clean_buf
    
    continuation_prompt = (
        "You are an expert JSON reconstruction system. "
        "The following JSON response was cut off mid-generation due to a network stream interruption:\n\n"
        f"--- TRUNCATED TAIL ---\n...{tail_context}\n--- END TAIL ---\n\n"
        "TASK:\n"
        "1. Identify the exact property, string, or object that was cut off.\n"
        "2. Complete the remaining properties, approaches, and items.\n"
        "3. Close all open strings, arrays, and braces to produce complete, valid JSON.\n"
        "4. Output ONLY the continuation text that immediately follows the truncated tail. "
        "Do NOT repeat the snippet above, and do NOT wrap in conversational text."
    )
    
    logger.info(f"Dispatching lightweight tail continuation request to {model} (tail size: {len(tail_context)} chars)...")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": continuation_prompt}],
            temperature=temperature,
            max_tokens=4096,
            timeout=timeout,
            stream=False
        )
        continuation_text = response.choices[0].message.content or ""
        logger.info(f"Continuation received ({len(continuation_text)} chars). Splicing with buffer...")
        
        # Clean fences from continuation
        continuation_clean = clean_json_fences(continuation_text)
        
        # If the continuation tried to repeat the root opening, strip it
        if continuation_clean.startswith("{") and clean_buf.count("{") > 1:
            continuation_clean = continuation_clean[1:].strip()
            
        combined = clean_buf + "\n" + continuation_clean
        return combined
    except Exception as cont_err:
        logger.error(f"Tail continuation request failed: {cont_err}")
        return truncated_buffer


def execute_resilient_llm_call(
    client: OpenAI,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = LLM_TEMPERATURE,
    top_p: float = LLM_TOP_P,
    max_tokens: int = LLM_MAX_TOKENS,
    stream: bool = True,
    stream_callback: Optional[Callable[[str], None]] = None,
    status_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    non_streaming_timeout: float = LLM_NON_STREAMING_TIMEOUT,
    extra_body: Optional[Dict[str, Any]] = None,
    save_buffer_path: Optional[Path] = None,
    fallback_list_key: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Executes an LLM call with a multi-strategy resilience architecture:
    1. If stream=True, persists chunks live into a buffer and to disk if save_buffer_path is provided.
    2. Reports live token count, speed (tok/s), connection mode, and active subprocess.
    3. If the stream cuts off or errors mid-generation, preserves the buffer!
    4. Detects truncation. If truncated, attempts AST repair -> Tail continuation to SAME model.
    5. If buffer was empty or continuation fails, falls back to stream=False with a 7-minute (420s) timeout.
    6. Returns (parsed_json_dict, raw_response_text).
    """
    accumulated_chunks: List[str] = []
    stream_severed = False
    stream_error_msg = ""
    start_time = time.time()
    token_count = 0
    prompt_len = sum(len(m.get("content", "")) for m in messages)
    
    buf_file = None
    if save_buffer_path:
        save_buffer_path.parent.mkdir(parents=True, exist_ok=True)
        buf_file = open(save_buffer_path, "w", encoding="utf-8")

    if status_callback:
        status_callback({
            "mode": "streaming" if stream else "non-streaming",
            "token_count": 0,
            "tokens_per_sec": 0.0,
            "subprocess_name": f"Ingesting context ({prompt_len} chars), awaiting TTFT...",
            "model": model
        })
            
    # ─── Stage 1: Streaming Execution with Live Buffer Persistence ───────────
    if stream:
        try:
            logger.info(f"Opening live resilient stream with {model}...")
            response_stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                extra_body=extra_body,
                stream=True
            )
            
            for chunk in response_stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                text_piece = delta.content if delta and delta.content is not None else None
                if text_piece:
                    accumulated_chunks.append(text_piece)
                    token_count += 1
                    now = time.time()
                    elapsed = now - start_time
                    tok_s = round(token_count / elapsed, 1) if elapsed > 0 else 0.0

                    if stream_callback:
                        stream_callback(text_piece)
                    if buf_file:
                        buf_file.write(text_piece)
                        if token_count % 30 == 0:
                            buf_file.flush()

                    if status_callback and (token_count % 15 == 0 or token_count == 1):
                        status_callback({
                            "mode": "streaming",
                            "token_count": token_count,
                            "tokens_per_sec": tok_s,
                            "subprocess_name": f"Streaming {model.split('/')[-1]} tokens",
                            "model": model
                        })
                            
        except Exception as s_err:
            stream_severed = True
            stream_error_msg = str(s_err)
            logger.warning(f"Live stream interrupted / severed: {s_err}. Preserving accumulated buffer ({len(accumulated_chunks)} chunks)...")
            if status_callback:
                status_callback({
                    "mode": "continuation",
                    "subprocess_name": f"Stream severed ({str(s_err)[:32]}...), preserving buffer",
                    "model": model
                })
        finally:
            if buf_file and not buf_file.closed:
                buf_file.flush()
                buf_file.close()
                buf_file = None

    response_text = "".join(accumulated_chunks).strip()
    del accumulated_chunks  # Immediately release individual chunk strings from heap
    
    # ─── Stage 2: Truncation Evaluation & Continuation ───────────────────────
    if response_text:
        incomplete, reason = is_json_incomplete(response_text)
        if not incomplete and not stream_severed:
            # Clean, complete response!
            try:
                parsed = resilient_json_parse(response_text, fallback_list_key=fallback_list_key)
                if status_callback:
                    status_callback({
                        "mode": "streaming",
                        "token_count": token_count,
                        "subprocess_name": "Response complete, JSON parsed successfully",
                        "model": model
                    })
                # Clean up transient buffer file on clean success to prevent disk accumulation
                if save_buffer_path and save_buffer_path.exists():
                    try:
                        save_buffer_path.unlink()
                    except OSError:
                        pass
                return parsed, response_text
            except Exception as parse_err:
                logger.warning(f"Direct parse of complete response encountered issue: {parse_err}")
                
        # Truncated or stream severed!
        logger.warning(f"Detected truncated response ({reason}). Initiating resilience recovery...")
        
        # Strategy 2: Try deterministic AST repair first (zero network cost)
        if status_callback:
            status_callback({
                "mode": "ast-repair",
                "subprocess_name": "Deterministic AST repair via json_repair",
                "model": model
            })
        try:
            repaired_text = repair_json(clean_json_fences(response_text))
            parsed = json.loads(repaired_text)
            # Verify if repaired payload has valid content
            if fallback_list_key and fallback_list_key in parsed and len(parsed[fallback_list_key]) > 0:
                logger.info(f"Fast AST repair succeeded: Recovered {len(parsed[fallback_list_key])} items.")
                if status_callback:
                    status_callback({
                        "mode": "ast-repair",
                        "subprocess_name": f"Fast AST repair recovered {len(parsed[fallback_list_key])} items",
                        "model": model
                    })
                return parsed, repaired_text
            elif not fallback_list_key and parsed:
                return parsed, repaired_text
        except Exception as r_err:
            logger.warning(f"Immediate AST repair was insufficient: {r_err}")

        # Strategy 3: Tail continuation to SAME model
        logger.info("Attempting in-flight continuation with the same LLM...")
        if status_callback:
            status_callback({
                "mode": "continuation",
                "subprocess_name": f"Dispatching tail continuation to {model.split('/')[-1]}",
                "model": model
            })
        continued_text = request_tail_continuation(
            client=client,
            model=model,
            truncated_buffer=response_text,
            timeout=90.0,
            temperature=0.2
        )
        try:
            parsed = resilient_json_parse(continued_text, fallback_list_key=fallback_list_key)
            logger.info("Successfully stitched continuation and parsed complete JSON!")
            if status_callback:
                status_callback({
                    "mode": "continuation",
                    "subprocess_name": "Tail continuation successfully stitched",
                    "model": model
                })
            return parsed, continued_text
        except Exception as cont_parse_err:
            logger.warning(f"Continuation stitching failed: {cont_parse_err}")

    # ─── Stage 4: Non-Streaming Fallback with 7-Minute Timeout ────────────────
    logger.info(f"Falling back to non-streaming execution with extended {non_streaming_timeout}s (7 min) timeout...")
    if status_callback:
        status_callback({
            "mode": "non-streaming",
            "subprocess_name": f"Non-streaming HTTP fallback (7 min timeout)",
            "model": model
        })
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            extra_body=extra_body,
            timeout=non_streaming_timeout,  # 7-minute timeout
            stream=False
        )
        non_stream_text = completion.choices[0].message.content or ""
        parsed = resilient_json_parse(non_stream_text, fallback_list_key=fallback_list_key)
        return parsed, non_stream_text
    except Exception as ns_err:
        logger.error(f"Non-streaming 7-minute fallback failed: {ns_err}")
        # Final salvage from previous buffer if available
        if response_text:
            logger.info("Attempting last-resort semantic salvage from accumulated stream buffer...")
            parsed = resilient_json_parse(response_text, default={}, fallback_list_key=fallback_list_key)
            if parsed:
                return parsed, response_text
        raise ns_err
