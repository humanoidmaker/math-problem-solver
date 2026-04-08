import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException

from ..core.auth import get_current_user
from ..core.database import get_db
from ..ml.math_solver import solve, solve_text
from ..models.schemas import SolveTextRequest

router = APIRouter(prefix="/api/solve", tags=["solve"])


@router.post("/image")
async def solve_image(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 10MB")

    result = solve(image_bytes)

    db = get_db()
    problem_doc = {
        "user_id": user["_id"],
        "source": "image",
        "filename": file.filename,
        "expression": result["expression"],
        "parsed": result["parsed"],
        "solution": result["solution"],
        "steps": result["steps"],
        "type": result["type"],
        "confidence": result["confidence"],
        "created_at": datetime.now(timezone.utc),
    }
    insert = await db.problems.insert_one(problem_doc)

    return {"id": str(insert.inserted_id), **result}


@router.post("/text")
async def solve_from_text(data: SolveTextRequest, user=Depends(get_current_user)):
    if not data.expression.strip():
        raise HTTPException(status_code=400, detail="Expression cannot be empty")

    result = solve_text(data.expression)

    db = get_db()
    problem_doc = {
        "user_id": user["_id"],
        "source": "text",
        "expression": result["expression"],
        "parsed": result["parsed"],
        "solution": result["solution"],
        "steps": result["steps"],
        "type": result["type"],
        "confidence": result["confidence"],
        "created_at": datetime.now(timezone.utc),
    }
    insert = await db.problems.insert_one(problem_doc)

    return {"id": str(insert.inserted_id), **result}


@router.get("/history")
async def get_history(skip: int = 0, limit: int = 20, user=Depends(get_current_user)):
    db = get_db()
    cursor = db.problems.find({"user_id": user["_id"]}).sort("created_at", -1).skip(skip).limit(limit)
    problems = []
    async for p in cursor:
        problems.append({
            "id": str(p["_id"]),
            "expression": p.get("expression", ""),
            "parsed": p.get("parsed", ""),
            "type": p.get("type", ""),
            "source": p.get("source", ""),
            "confidence": p.get("confidence", 0),
            "solution": p.get("solution", {}),
            "steps": p.get("steps", []),
            "created_at": p["created_at"].isoformat(),
        })
    return problems


@router.get("/stats")
async def get_stats(user=Depends(get_current_user)):
    db = get_db()
    total = await db.problems.count_documents({"user_id": user["_id"]})

    type_pipeline = [
        {"$match": {"user_id": user["_id"]}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
    ]
    types = await db.problems.aggregate(type_pipeline).to_list(20)

    source_pipeline = [
        {"$match": {"user_id": user["_id"]}},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    ]
    sources = await db.problems.aggregate(source_pipeline).to_list(10)

    avg_pipeline = [
        {"$match": {"user_id": user["_id"]}},
        {"$group": {"_id": None, "avg_confidence": {"$avg": "$confidence"}}},
    ]
    avg_result = await db.problems.aggregate(avg_pipeline).to_list(1)
    avg_conf = avg_result[0]["avg_confidence"] if avg_result else 0

    return {
        "total_problems": total,
        "avg_confidence": round(avg_conf or 0, 1),
        "by_type": {t["_id"]: t["count"] for t in types if t["_id"]},
        "by_source": {s["_id"]: s["count"] for s in sources if s["_id"]},
    }


# Practice problems generator
PRACTICE_PROBLEMS = {
    "arithmetic": [
        "24 + 37", "156 - 89", "12 * 15", "144 / 12",
        "3.5 + 2.7", "100 - 47.5", "25 * 4.2", "81 / 9",
        "15 + 28 - 13", "7 * 8 + 12", "(15 + 9) * 3", "120 / (4 + 6)",
    ],
    "algebra": [
        "2*x + 5 = 15", "3*x - 7 = 20", "x/4 + 3 = 10", "5*x = 45",
        "2*x + 3*x = 25", "4*(x + 2) = 24", "x + 7 = 3*x - 1",
        "2*(x - 3) = x + 4", "x/2 + x/3 = 5", "3*x + 2 = 2*x + 9",
    ],
    "equations": [
        "x**2 - 9 = 0", "x**2 + 5*x + 6 = 0", "x**2 - 4*x + 4 = 0",
        "2*x**2 - 8 = 0", "x**2 - 7*x + 12 = 0", "x**2 + 2*x - 15 = 0",
        "3*x**2 - 12*x = 0", "x**2 - 1 = 0", "x**2 + 6*x + 9 = 0",
    ],
}


@router.get("/practice")
async def get_practice(difficulty: str = "arithmetic", user=Depends(get_current_user)):
    problems = PRACTICE_PROBLEMS.get(difficulty, PRACTICE_PROBLEMS["arithmetic"])
    selected = random.sample(problems, min(5, len(problems)))
    return {"difficulty": difficulty, "problems": selected}
