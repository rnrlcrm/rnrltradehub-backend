"""
Report export API endpoints for generating Excel, PDF, and CSV reports.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from services.report_service import ReportService


# Router for report exports
export_router = APIRouter(prefix="/api/reports", tags=["Reports & Export"])


@export_router.get("/business-partners/csv")
def export_business_partners_csv(
    business_type: Optional[str] = None,
    bp_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export business partners to CSV format.
    
    Query Parameters:
    - business_type: Filter by business type (BUYER, SELLER, BOTH, AGENT)
    - bp_status: Filter by status (ACTIVE, INACTIVE, etc.)
    """
    report_service = ReportService(db)
    
    filters = {}
    if business_type:
        filters['business_type'] = business_type
    if bp_status:
        filters['status'] = bp_status
    
    data = report_service.get_business_partners_data(filters)
    csv_content = report_service.export_to_csv(data)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=business_partners_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@export_router.get("/business-partners/excel")
def export_business_partners_excel(
    business_type: Optional[str] = None,
    bp_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export business partners to Excel format.
    
    Query Parameters:
    - business_type: Filter by business type (BUYER, SELLER, BOTH, AGENT)
    - bp_status: Filter by status (ACTIVE, INACTIVE, etc.)
    """
    report_service = ReportService(db)
    
    filters = {}
    if business_type:
        filters['business_type'] = business_type
    if bp_status:
        filters['status'] = bp_status
    
    data = report_service.get_business_partners_data(filters)
    
    try:
        excel_bytes = report_service.export_to_excel(data, sheet_name="Business Partners")
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=business_partners_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )


@export_router.get("/business-partners/pdf")
def export_business_partners_pdf(
    business_type: Optional[str] = None,
    bp_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export business partners to PDF format.
    
    Query Parameters:
    - business_type: Filter by business type (BUYER, SELLER, BOTH, AGENT)
    - bp_status: Filter by status (ACTIVE, INACTIVE, etc.)
    """
    report_service = ReportService(db)
    
    filters = {}
    if business_type:
        filters['business_type'] = business_type
    if bp_status:
        filters['status'] = bp_status
    
    data = report_service.get_business_partners_data(filters)
    
    try:
        pdf_bytes = report_service.export_to_pdf(data, title="Business Partners Report")
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=business_partners_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        }
    )


@export_router.get("/sales-contracts/csv")
def export_sales_contracts_csv(
    contract_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export sales contracts to CSV format.
    
    Query Parameters:
    - contract_status: Filter by contract status
    """
    report_service = ReportService(db)
    
    filters = {}
    if contract_status:
        filters['status'] = contract_status
    
    data = report_service.get_sales_contracts_data(filters)
    csv_content = report_service.export_to_csv(data)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=sales_contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@export_router.get("/sales-contracts/excel")
def export_sales_contracts_excel(
    contract_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export sales contracts to Excel format.
    
    Query Parameters:
    - contract_status: Filter by contract status
    """
    report_service = ReportService(db)
    
    filters = {}
    if contract_status:
        filters['status'] = contract_status
    
    data = report_service.get_sales_contracts_data(filters)
    
    try:
        excel_bytes = report_service.export_to_excel(data, sheet_name="Sales Contracts")
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=sales_contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )


@export_router.get("/sales-contracts/pdf")
def export_sales_contracts_pdf(
    contract_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export sales contracts to PDF format.
    
    Query Parameters:
    - contract_status: Filter by contract status
    """
    report_service = ReportService(db)
    
    filters = {}
    if contract_status:
        filters['status'] = contract_status
    
    data = report_service.get_sales_contracts_data(filters)
    
    try:
        pdf_bytes = report_service.export_to_pdf(data, title="Sales Contracts Report")
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=sales_contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        }
    )


@export_router.get("/invoices/csv")
def export_invoices_csv(
    invoice_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export invoices to CSV format.
    
    Query Parameters:
    - invoice_status: Filter by invoice status (draft, sent, paid, overdue, etc.)
    """
    report_service = ReportService(db)
    
    filters = {}
    if invoice_status:
        filters['status'] = invoice_status
    
    data = report_service.get_invoices_data(filters)
    csv_content = report_service.export_to_csv(data)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@export_router.get("/invoices/excel")
def export_invoices_excel(
    invoice_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export invoices to Excel format.
    
    Query Parameters:
    - invoice_status: Filter by invoice status (draft, sent, paid, overdue, etc.)
    """
    report_service = ReportService(db)
    
    filters = {}
    if invoice_status:
        filters['status'] = invoice_status
    
    data = report_service.get_invoices_data(filters)
    
    try:
        excel_bytes = report_service.export_to_excel(data, sheet_name="Invoices")
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )


@export_router.get("/invoices/pdf")
def export_invoices_pdf(
    invoice_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export invoices to PDF format.
    
    Query Parameters:
    - invoice_status: Filter by invoice status (draft, sent, paid, overdue, etc.)
    """
    report_service = ReportService(db)
    
    filters = {}
    if invoice_status:
        filters['status'] = invoice_status
    
    data = report_service.get_invoices_data(filters)
    
    try:
        pdf_bytes = report_service.export_to_pdf(data, title="Invoices Report")
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        }
    )


# Import datetime for filename generation
from datetime import datetime
