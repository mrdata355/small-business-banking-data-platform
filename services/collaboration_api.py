from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

from collaboration.recommendation_engine import WorkItem, default_engine

DATABASE_URL = os.environ.get("DATABASE_URL")
app = FastAPI(title="Oakbridge Collaboration Graph", version="1.0.0")


class WorkItemCreate(BaseModel):
    title: str = Field(min_length=4, max_length=240)
    description: str = Field(min_length=4, max_length=5000)
    work_type: str = "TASK"
    priority: str = "P2"
    requester_department: str
    owner_department: str
    owner_name: str | None = None
    pipeline_component: str | None = None
    source_ref: str | None = None
    due_at: datetime | None = None
    estimated_hours: float | None = Field(default=None, ge=0)
    business_value: float = Field(default=5, ge=0, le=10)
    risk_reduction: float = Field(default=5, ge=0, le=10)
    urgency_score: float = Field(default=5, ge=0, le=10)
    effort_score: float = Field(default=3, gt=0, le=10)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkItemPatch(BaseModel):
    status: str | None = None
    priority: str | None = None
    owner_name: str | None = None
    owner_department: str | None = None
    business_value: float | None = Field(default=None, ge=0, le=10)
    risk_reduction: float | None = Field(default=None, ge=0, le=10)
    urgency_score: float | None = Field(default=None, ge=0, le=10)
    effort_score: float | None = Field(default=None, gt=0, le=10)


def connect():
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def _department_id(cur, code: str):
    cur.execute("SELECT department_id FROM departments WHERE department_code=%s", (code,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail=f"Unknown department {code}")
    return row["department_id"]


@app.get("/health")
def health():
    return {"status": "ok", "service": "collaboration-api", "ts": datetime.now(timezone.utc).isoformat()}


@app.get("/departments")
def departments():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM departments ORDER BY department_name")
        return cur.fetchall()


@app.get("/work-items")
def work_items(status: str | None = None, owner_department: str | None = None):
    sql = "SELECT * FROM sem_work_queue WHERE 1=1"
    params: list[Any] = []
    if status:
        sql += " AND status=%s"; params.append(status)
    if owner_department:
        sql += " AND owner_department=%s"; params.append(owner_department)
    sql += " ORDER BY recommendation_score DESC, created_at ASC"
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


@app.post("/work-items")
def create_work_item(body: WorkItemCreate):
    with connect() as conn, conn.cursor() as cur:
        requester_id = _department_id(cur, body.requester_department)
        owner_id = _department_id(cur, body.owner_department)
        cur.execute("SELECT COALESCE(MAX((regexp_match(work_key, '[0-9]+$'))[1]::int),0)+1 AS n FROM work_items")
        n = cur.fetchone()["n"]
        key = f"OB-{n:05d}"
        cur.execute(
            """
            INSERT INTO work_items(
              work_key,title,description,work_type,status,priority,
              requester_department_id,owner_department_id,owner_name,pipeline_component,
              source_ref,due_at,estimated_hours,business_value,risk_reduction,
              urgency_score,effort_score,metadata
            ) VALUES (%s,%s,%s,%s,'BACKLOG',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
            """,
            (key, body.title, body.description, body.work_type, body.priority,
             requester_id, owner_id, body.owner_name, body.pipeline_component,
             body.source_ref, body.due_at, body.estimated_hours, body.business_value,
             body.risk_reduction, body.urgency_score, body.effort_score, body.metadata),
        )
        row = cur.fetchone()
        cur.execute("INSERT INTO work_item_events(work_item_id,event_type,actor,to_value,detail) VALUES(%s,'CREATED','collaboration-api','BACKLOG',%s)", (row["work_item_id"], {"source_ref": body.source_ref}))
        conn.commit()
        return row


@app.patch("/work-items/{work_key}")
def update_work_item(work_key: str, body: WorkItemPatch):
    fields: list[str] = []
    params: list[Any] = []
    with connect() as conn, conn.cursor() as cur:
        if body.status is not None:
            fields.append("status=%s"); params.append(body.status)
        if body.priority is not None:
            fields.append("priority=%s"); params.append(body.priority)
        if body.owner_name is not None:
            fields.append("owner_name=%s"); params.append(body.owner_name)
        if body.owner_department is not None:
            fields.append("owner_department_id=%s"); params.append(_department_id(cur, body.owner_department))
        for column in ("business_value", "risk_reduction", "urgency_score", "effort_score"):
            value = getattr(body, column)
            if value is not None:
                fields.append(f"{column}=%s"); params.append(value)
        if not fields:
            raise HTTPException(status_code=400, detail="No supported fields supplied")
        fields.append("updated_at=now()")
        params.append(work_key)
        cur.execute(f"UPDATE work_items SET {', '.join(fields)} WHERE work_key=%s RETURNING *", params)
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Work item not found")
        conn.commit()
        return row


@app.get("/recommendations/{department}")
def recommendations(department: str):
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM sem_work_queue WHERE status NOT IN ('DONE','CANCELLED')")
        rows = cur.fetchall()
    items = [
        WorkItem(
            work_key=r["work_key"], title=r["title"], department=(r["owner_department"] or department).upper().replace(" ", "_"),
            requester_department=(r["requester_department"] or "PRODUCT").upper().replace(" ", "_"),
            status=r["status"], priority=r["priority"], business_value=float(r["business_value"] or 0),
            risk_reduction=float(r["risk_reduction"] or 0), urgency=float(r["urgency_score"] or 0),
            effort=float(r["effort_score"] or 1), github_ref=None,
        ) for r in rows
    ]
    engine = default_engine()
    if department not in engine.objectives:
        raise HTTPException(status_code=404, detail=f"No objective model for department {department}")
    return [
        {
            "work_key": item.work_item.work_key,
            "title": item.work_item.title,
            "score": round(item.score, 4),
            "predicted_helpfulness": round(item.predicted_helpfulness, 4),
            "next_action": item.next_action,
            "rationale": item.rationale,
        }
        for item in engine.rank_for_department(department, items)[:25]
    ]
