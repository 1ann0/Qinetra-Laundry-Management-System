"""Owner-only report previews and bounded spreadsheet downloads."""
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import text
import auth
from database import get_db
from owner_reports import build_report, csv_report, xlsx_report, json_report

router = APIRouter(prefix="/dashboard/reports", dependencies=[Depends(auth.require_owner)], tags=["Owner reports"])


def report_filters(request: Request, start_date: date | None = None, end_date: date | None = None,
                   customer_id: int | None = Query(None, gt=0), service_id: int | None = Query(None, gt=0),
                   status: str | None = None, payment_method: str | None = None, attention: str | None = None,
                   category: str | None = None):
    allowed = {"start_date", "end_date", "customer_id", "service_id", "status", "payment_method", "attention", "category"}
    if request.url.path.endswith("/download"):
        allowed.add("format")
    if set(request.query_params) - allowed or len(request.query_params.multi_items()) != len(request.query_params):
        raise HTTPException(422, "Choose valid report filters without repeated fields")
    return {"start_date": start_date, "end_date": end_date, "customer_id": customer_id, "service_id": service_id,
            "status": status, "payment_method": payment_method, "attention": attention, "category":category}


@contextmanager
def read_snapshot(db):
    if db.get_bind().dialect.name == "postgresql":
        # Authentication has finished its read; every report query now sees one read-only snapshot.
        db.rollback()
        db.connection(execution_options={"isolation_level": "REPEATABLE READ"})
        db.execute(text("SET TRANSACTION READ ONLY"))
    try:
        yield db
    finally:
        db.rollback()


@router.get("/{report_name}")
def report_json(report_name: str, filters: dict = Depends(report_filters), db: Session = Depends(get_db)):
    with read_snapshot(db):
        report = build_report(db, report_name, **filters)
    return Response(json_report(report), media_type="application/json")


@router.get("/{report_name}/download")
def report_download(report_name: str, format: Literal["xlsx", "csv"] = "xlsx",
                    filters: dict = Depends(report_filters), db: Session = Depends(get_db)):
    with read_snapshot(db):
        report = build_report(db, report_name, **filters)
    period = "_".join(str(value) for value in (filters["start_date"], filters["end_date"]) if value) or "current"
    generated = datetime.fromisoformat(report["generated_at"]).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"qlms_{report_name}_{period}_{generated}.{format}"
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv; charset=utf-8"
    return Response(xlsx_report(report) if format == "xlsx" else csv_report(report), media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
