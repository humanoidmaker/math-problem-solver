"""
MathLens Math Problem Solver.

Pipeline:
1. OCR — TrOCR to read handwritten/printed math from image
2. Parse — convert OCR text to mathematical expression
3. Solve — SymPy for symbolic computation
4. Generate step-by-step solution
"""

import re
import logging
from typing import Dict, Any, List, Optional

import cv2
import numpy as np
import torch
from PIL import Image
import sympy
from sympy import (
    symbols, sympify, solve as sym_solve, Eq, diff, integrate,
    sqrt, Rational, oo, simplify, factor, expand, latex,
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
    convert_xor,
)

logger = logging.getLogger(__name__)

_model = None
_processor = None
_device = None

x, y, z = symbols("x y z")

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor,)


def load_model(model_name: str = "microsoft/trocr-base-handwritten", use_gpu: bool = True):
    global _model, _processor, _device
    if _model is not None:
        return

    _device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
    logger.info(f"Loading OCR model on {_device}...")

    try:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        _processor = TrOCRProcessor.from_pretrained(model_name)
        _model = VisionEncoderDecoderModel.from_pretrained(model_name).to(_device)
        _model.eval()
        logger.info("TrOCR model loaded for math OCR")
    except Exception as e:
        logger.warning(f"Failed to load TrOCR: {e}")
        _model = None
        _processor = None


def _ocr_image(image_bytes: bytes) -> tuple:
    """Run OCR on image. Returns (text, confidence)."""
    global _model, _processor, _device

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    if _model is not None and _processor is not None:
        pil_img = Image.fromarray(binary).convert("RGB")
        pixel_values = _processor(images=pil_img, return_tensors="pt").pixel_values.to(_device)

        with torch.no_grad():
            outputs = _model.generate(
                pixel_values,
                max_new_tokens=128,
                output_scores=True,
                return_dict_in_generate=True,
            )

        text = _processor.batch_decode(outputs.sequences, skip_special_tokens=True)[0]
        if outputs.scores:
            probs = [torch.softmax(s, dim=-1).max().item() for s in outputs.scores]
            confidence = round(sum(probs) / len(probs) * 100, 1) if probs else 50.0
        else:
            confidence = 75.0
        return text.strip(), confidence

    return "[Model not loaded]", 0.0


def _clean_ocr_text(text: str) -> str:
    """Apply common OCR corrections for math expressions."""
    text = text.strip()
    # Common OCR mistakes
    text = text.replace("×", "*").replace("÷", "/").replace("−", "-")
    text = text.replace("＝", "=").replace("＋", "+")
    text = re.sub(r"\bX\b", "x", text)  # Capital X -> variable x
    text = re.sub(r"(\d)\s*[xX]\s*(\d)", r"\1*\2", text)  # 3x4 -> 3*4 when between digits
    text = re.sub(r"(\d)\s*[xX]\s*([^=\d])", r"\1*x", text)  # keep x as variable before =
    text = text.replace("^", "**")
    text = re.sub(r"(\d)\s*\^\s*(\d)", r"\1**\2", text)
    # sqrt symbol
    text = re.sub(r"[√]\s*\(([^)]+)\)", r"sqrt(\1)", text)
    text = re.sub(r"[√]\s*(\d+)", r"sqrt(\1)", text)
    return text


def _detect_problem_type(expr_str: str) -> str:
    """Detect what type of math problem this is."""
    if "=" in expr_str:
        left, right = expr_str.split("=", 1)
        # Check for quadratic
        if re.search(r"x\s*\*\*\s*2|x\^2|x²", expr_str):
            return "quadratic_equation"
        if any(v in expr_str for v in ["x", "y", "z"]):
            return "linear_equation"
        return "equation"

    if re.search(r"\bd/dx\b|derivative|diff", expr_str, re.IGNORECASE):
        return "derivative"
    if re.search(r"\bintegral\b|\bintegrate\b|\bint\b", expr_str, re.IGNORECASE):
        return "integral"
    if any(v in expr_str for v in ["x", "y", "z"]):
        return "expression"
    return "arithmetic"


def _parse_expression(text: str) -> tuple:
    """Parse cleaned text into SymPy expression(s). Returns (parsed_str, expr_or_eq, type)."""
    cleaned = _clean_ocr_text(text)
    prob_type = _detect_problem_type(cleaned)

    try:
        if "=" in cleaned:
            parts = cleaned.split("=", 1)
            left = parse_expr(parts[0].strip(), transformations=TRANSFORMATIONS)
            right = parse_expr(parts[1].strip(), transformations=TRANSFORMATIONS)
            eq = Eq(left, right)
            parsed_str = f"{left} = {right}"
            return parsed_str, eq, prob_type

        if prob_type == "derivative":
            expr_part = re.sub(r"d/dx\s*|derivative\s*(of)?\s*|diff\s*", "", cleaned, flags=re.IGNORECASE).strip()
            expr = parse_expr(expr_part, transformations=TRANSFORMATIONS)
            return f"d/dx({expr})", expr, "derivative"

        if prob_type == "integral":
            expr_part = re.sub(r"integral\s*(of)?\s*|integrate\s*|int\s*", "", cleaned, flags=re.IGNORECASE).strip()
            expr_part = re.sub(r"\s*dx\s*$", "", expr_part)
            expr = parse_expr(expr_part, transformations=TRANSFORMATIONS)
            return f"integral({expr}) dx", expr, "integral"

        expr = parse_expr(cleaned, transformations=TRANSFORMATIONS)
        return str(expr), expr, prob_type

    except Exception as e:
        logger.warning(f"Parse error for '{cleaned}': {e}")
        raise ValueError(f"Could not parse expression: {text}")


def _generate_steps_arithmetic(expr) -> tuple:
    """Solve arithmetic expression with steps."""
    result = expr.evalf()
    simplified = simplify(expr)
    steps = [str(expr)]
    if simplified != expr:
        steps.append(f"= {simplified}")
    steps.append(f"= {result}")
    return {"result": float(result)}, steps


def _generate_steps_linear(eq) -> tuple:
    """Solve linear equation with steps."""
    left = eq.lhs
    right = eq.rhs
    var = list(eq.free_symbols)[0] if eq.free_symbols else x

    steps = [f"{left} = {right}"]

    moved = left - right
    steps.append(f"{moved} = 0")

    solution = sym_solve(eq, var)
    if solution:
        sol = solution[0]
        steps.append(f"{var} = {sol}")
        return {str(var): str(sol)}, steps

    return {"error": "No solution found"}, steps


def _generate_steps_quadratic(eq) -> tuple:
    """Solve quadratic equation with steps."""
    left = eq.lhs
    right = eq.rhs
    var = list(eq.free_symbols)[0] if eq.free_symbols else x

    expr = left - right
    expr = expand(expr)
    steps = [f"{left} = {right}"]
    steps.append(f"{expr} = 0")

    # Extract coefficients
    poly = sympy.Poly(expr, var)
    coeffs = poly.all_coeffs()
    if len(coeffs) == 3:
        a, b, c = coeffs
        steps.append(f"a = {a}, b = {b}, c = {c}")
        discriminant = b**2 - 4*a*c
        steps.append(f"Discriminant = b^2 - 4ac = {b}^2 - 4({a})({c}) = {discriminant}")

        if discriminant >= 0:
            steps.append(f"{var} = (-b +/- sqrt(discriminant)) / 2a")

    solutions = sym_solve(eq, var)
    sol_dict = {}
    for i, sol in enumerate(solutions):
        key = f"{var}_{i+1}" if len(solutions) > 1 else str(var)
        sol_dict[key] = str(sol)
        steps.append(f"{var} = {sol}")

    return sol_dict, steps


def _generate_steps_derivative(expr) -> tuple:
    """Compute derivative with steps."""
    var = list(expr.free_symbols)[0] if expr.free_symbols else x
    steps = [f"d/d{var}({expr})"]

    result = diff(expr, var)
    simplified = simplify(result)

    steps.append(f"= {result}")
    if simplified != result:
        steps.append(f"= {simplified}")

    return {"derivative": str(simplified)}, steps


def _generate_steps_integral(expr) -> tuple:
    """Compute integral with steps."""
    var = list(expr.free_symbols)[0] if expr.free_symbols else x
    steps = [f"integral({expr}) d{var}"]

    result = integrate(expr, var)
    simplified = simplify(result)

    steps.append(f"= {result} + C")
    if simplified != result:
        steps.append(f"= {simplified} + C")

    return {"integral": f"{simplified} + C"}, steps


def solve_text(text: str) -> Dict[str, Any]:
    """Solve a math problem from text input."""
    try:
        parsed_str, expr_or_eq, prob_type = _parse_expression(text)
    except ValueError as e:
        return {
            "expression": text,
            "parsed": text,
            "solution": {"error": str(e)},
            "steps": [text, "Error: Could not parse expression"],
            "type": "unknown",
            "confidence": 0,
        }

    try:
        if prob_type == "arithmetic":
            solution, steps = _generate_steps_arithmetic(expr_or_eq)
        elif prob_type == "linear_equation" or prob_type == "equation":
            solution, steps = _generate_steps_linear(expr_or_eq)
        elif prob_type == "quadratic_equation":
            solution, steps = _generate_steps_quadratic(expr_or_eq)
        elif prob_type == "derivative":
            solution, steps = _generate_steps_derivative(expr_or_eq)
        elif prob_type == "integral":
            solution, steps = _generate_steps_integral(expr_or_eq)
        elif prob_type == "expression":
            simplified = simplify(expr_or_eq)
            factored = factor(expr_or_eq)
            steps = [str(expr_or_eq)]
            if simplified != expr_or_eq:
                steps.append(f"Simplified: {simplified}")
            if factored != expr_or_eq and factored != simplified:
                steps.append(f"Factored: {factored}")
            solution = {"simplified": str(simplified), "factored": str(factored)}
        else:
            solution = {"result": str(simplify(expr_or_eq))}
            steps = [str(expr_or_eq), f"= {simplify(expr_or_eq)}"]

        return {
            "expression": text,
            "parsed": parsed_str,
            "solution": solution,
            "steps": steps,
            "type": prob_type,
            "confidence": 95,
        }

    except Exception as e:
        logger.error(f"Solve error: {e}")
        return {
            "expression": text,
            "parsed": parsed_str,
            "solution": {"error": str(e)},
            "steps": [parsed_str, f"Error: {e}"],
            "type": prob_type,
            "confidence": 0,
        }


def solve(image_bytes: bytes) -> Dict[str, Any]:
    """Full pipeline: image -> OCR -> parse -> solve."""
    ocr_text, confidence = _ocr_image(image_bytes)

    if confidence == 0:
        return {
            "expression": ocr_text,
            "parsed": "",
            "solution": {"error": "OCR model not available"},
            "steps": [],
            "type": "unknown",
            "confidence": 0,
        }

    result = solve_text(ocr_text)
    result["confidence"] = min(confidence, result.get("confidence", 0))
    result["expression"] = ocr_text
    return result
