"""Generates the private, never-published enterprise API specs used for the cold-start
generalization test (DESIGN_DOC.md's "Cold-start validation set", previously an open item --
"not yet authored").

These are hand-authored OpenAPI 3.0 specs for enterprise domains (CRM, HRIS, Procurement, Ticket
Management, Asset Management) that do not correspond to any real, publicly-documented API. The
point is that a base LLM's pretraining data cannot plausibly contain paired examples for these
exact endpoint shapes, unlike GitHub/Stripe/Slack/Zoom/DigitalOcean/Spotify, all of which are
extremely well-documented public APIs a model may have seen during pretraining. This is the
sharpest test of RQ4 (does zero-execution generation actually solve cold-start, not just work on
APIs the model already half-knows).

Not real company APIs, not derived from any real company's internal documentation -- generic,
plausible enterprise SaaS shapes only.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "specs" / "private"

SECURITY_SCHEME = {
    "type": "apiKey",
    "in": "header",
    "name": "X-Internal-Api-Key",
}


def op(operation_id, description, params=None, body_schema=None, body_required=True):
    o = {"operationId": operation_id, "description": description, "responses": {"200": {"description": "OK"}}}
    if params:
        o["parameters"] = params
    if body_schema:
        o["requestBody"] = {
            "required": body_required,
            "content": {"application/json": {"schema": body_schema}},
        }
    return o


def path_param(name, type_="string"):
    return {"name": name, "in": "path", "required": True, "schema": {"type": type_}}


def query_param(name, type_="string", required=False):
    return {"name": name, "in": "query", "required": required, "schema": {"type": type_}}


def schema(required, properties):
    return {"type": "object", "required": required, "properties": properties}


SPECS = {
    "crm": {
        "title": "Internal CRM API",
        "version": "1.0.0",
        "paths": {
            "/customers/search": {
                "post": op(
                    "searchCustomers",
                    "Search the customer database by name, region, or account tier.",
                    body_schema=schema(
                        ["query"],
                        {
                            "query": {"type": "string"},
                            "region": {"type": "string"},
                            "account_tier": {"type": "string"},
                            "limit": {"type": "integer"},
                        },
                    ),
                )
            },
            "/customers/{customer_id}/risk": {
                "get": op(
                    "getCustomerRisk",
                    "Retrieve the churn-risk score and contributing factors for a customer account.",
                    params=[path_param("customer_id")],
                )
            },
            "/opportunities": {
                "post": op(
                    "createOpportunity",
                    "Create a new sales opportunity tied to a customer account.",
                    body_schema=schema(
                        ["customer_id", "stage", "estimated_value"],
                        {
                            "customer_id": {"type": "string"},
                            "stage": {"type": "string"},
                            "estimated_value": {"type": "number"},
                            "owner_email": {"type": "string"},
                            "close_date": {"type": "string"},
                        },
                    ),
                )
            },
            "/opportunities/{opportunity_id}/stage": {
                "patch": op(
                    "updateOpportunityStage",
                    "Advance or roll back an opportunity's pipeline stage.",
                    params=[path_param("opportunity_id")],
                    body_schema=schema(["stage"], {"stage": {"type": "string"}, "reason": {"type": "string"}}),
                )
            },
            "/contracts/{contract_id}": {
                "get": op(
                    "getContract",
                    "Retrieve contract terms, renewal date, and signatory details for a customer contract.",
                    params=[path_param("contract_id")],
                )
            },
            "/contracts": {
                "post": op(
                    "createContract",
                    "Create a new contract record linked to a customer and opportunity.",
                    body_schema=schema(
                        ["customer_id", "term_months", "annual_value"],
                        {
                            "customer_id": {"type": "string"},
                            "opportunity_id": {"type": "string"},
                            "term_months": {"type": "integer"},
                            "annual_value": {"type": "number"},
                        },
                    ),
                )
            },
        },
    },
    "hris": {
        "title": "Internal HRIS API",
        "version": "1.0.0",
        "paths": {
            "/employees/{employee_id}/onboard": {
                "post": op(
                    "onboardEmployee",
                    "Kick off the onboarding workflow for a newly hired employee: provisions accounts, assigns a manager, and schedules orientation.",
                    params=[path_param("employee_id")],
                    body_schema=schema(
                        ["start_date", "department", "manager_id"],
                        {
                            "start_date": {"type": "string"},
                            "department": {"type": "string"},
                            "manager_id": {"type": "string"},
                            "employment_type": {"type": "string"},
                        },
                    ),
                )
            },
            "/leave-requests": {
                "post": op(
                    "createLeaveRequest",
                    "Submit a leave-of-absence request for approval.",
                    body_schema=schema(
                        ["employee_id", "leave_type", "start_date", "end_date"],
                        {
                            "employee_id": {"type": "string"},
                            "leave_type": {"type": "string"},
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"},
                            "notes": {"type": "string"},
                        },
                    ),
                )
            },
            "/leave-requests/{request_id}/approve": {
                "post": op(
                    "approveLeaveRequest",
                    "Manager approval for a pending leave request.",
                    params=[path_param("request_id")],
                    body_schema=schema(["approver_id"], {"approver_id": {"type": "string"}, "comment": {"type": "string"}}),
                )
            },
            "/employees/{employee_id}/salary": {
                "get": op(
                    "getEmployeeSalary",
                    "Retrieve current compensation details for an employee. Restricted to HR and the employee's manager.",
                    params=[path_param("employee_id")],
                )
            },
            "/employees/{employee_id}/salary/adjust": {
                "post": op(
                    "adjustEmployeeSalary",
                    "Record a compensation change (raise, promotion adjustment, or correction).",
                    params=[path_param("employee_id")],
                    body_schema=schema(
                        ["new_annual_salary", "effective_date", "reason"],
                        {
                            "new_annual_salary": {"type": "number"},
                            "effective_date": {"type": "string"},
                            "reason": {"type": "string"},
                        },
                    ),
                )
            },
            "/benefits/enroll": {
                "post": op(
                    "enrollBenefits",
                    "Enroll an employee in a benefits plan during open enrollment or a qualifying life event.",
                    body_schema=schema(
                        ["employee_id", "plan_id"],
                        {
                            "employee_id": {"type": "string"},
                            "plan_id": {"type": "string"},
                            "dependents": {"type": "integer"},
                        },
                    ),
                )
            },
        },
    },
    "procurement": {
        "title": "Internal Procurement API",
        "version": "1.0.0",
        "paths": {
            "/purchase-orders": {
                "post": op(
                    "createPurchaseOrder",
                    "Create a purchase order against an approved vendor.",
                    body_schema=schema(
                        ["vendor_id", "line_items", "total_amount"],
                        {
                            "vendor_id": {"type": "string"},
                            "line_items": {"type": "array"},
                            "total_amount": {"type": "number"},
                            "cost_center": {"type": "string"},
                        },
                    ),
                )
            },
            "/purchase-orders/{po_id}/approve": {
                "post": op(
                    "approvePurchaseOrder",
                    "Approve a pending purchase order that exceeds the requester's auto-approval limit.",
                    params=[path_param("po_id")],
                    body_schema=schema(["approver_id"], {"approver_id": {"type": "string"}}),
                )
            },
            "/vendors": {
                "post": op(
                    "registerVendor",
                    "Register a new approved vendor for procurement.",
                    body_schema=schema(
                        ["legal_name", "tax_id", "payment_terms"],
                        {
                            "legal_name": {"type": "string"},
                            "tax_id": {"type": "string"},
                            "payment_terms": {"type": "string"},
                            "contact_email": {"type": "string"},
                        },
                    ),
                )
            },
            "/vendors/{vendor_id}": {
                "get": op(
                    "getVendor",
                    "Retrieve a vendor's compliance status, payment terms, and order history.",
                    params=[path_param("vendor_id")],
                )
            },
            "/inventory/{sku}": {
                "get": op(
                    "getInventoryLevel",
                    "Retrieve current on-hand inventory count and reorder threshold for a SKU.",
                    params=[path_param("sku")],
                )
            },
            "/approvals/{approval_id}/escalate": {
                "post": op(
                    "escalateApproval",
                    "Escalate a stalled purchase approval to the next level in the approval chain.",
                    params=[path_param("approval_id")],
                    body_schema=schema(["reason"], {"reason": {"type": "string"}}),
                )
            },
        },
    },
    "ticketing": {
        "title": "Internal Ticket Management API",
        "version": "1.0.0",
        "paths": {
            "/incidents": {
                "post": op(
                    "createIncident",
                    "Open a new incident ticket.",
                    body_schema=schema(
                        ["title", "severity", "reporter_id"],
                        {
                            "title": {"type": "string"},
                            "severity": {"type": "string"},
                            "reporter_id": {"type": "string"},
                            "affected_service": {"type": "string"},
                        },
                    ),
                )
            },
            "/incidents/{incident_id}/escalate": {
                "post": op(
                    "escalateIncident",
                    "Escalate an incident to the next on-call tier.",
                    params=[path_param("incident_id")],
                    body_schema=schema(["reason"], {"reason": {"type": "string"}, "target_tier": {"type": "string"}}),
                )
            },
            "/incidents/{incident_id}/resolve": {
                "post": op(
                    "resolveIncident",
                    "Mark an incident resolved and record the root-cause summary.",
                    params=[path_param("incident_id")],
                    body_schema=schema(
                        ["resolution_summary"],
                        {"resolution_summary": {"type": "string"}, "root_cause": {"type": "string"}},
                    ),
                )
            },
            "/slas/{sla_id}": {
                "get": op(
                    "getSlaStatus",
                    "Retrieve the SLA definition and current breach status for a ticket category.",
                    params=[path_param("sla_id")],
                )
            },
            "/incidents/{incident_id}/assign": {
                "patch": op(
                    "assignIncident",
                    "Reassign an incident to a different responder or team.",
                    params=[path_param("incident_id")],
                    body_schema=schema(["assignee_id"], {"assignee_id": {"type": "string"}}),
                )
            },
        },
    },
    "asset_management": {
        "title": "Internal Asset Management API",
        "version": "1.0.0",
        "paths": {
            "/assets/register": {
                "post": op(
                    "registerAsset",
                    "Register a new physical or software asset in the inventory system.",
                    body_schema=schema(
                        ["asset_type", "serial_number", "owner_department"],
                        {
                            "asset_type": {"type": "string"},
                            "serial_number": {"type": "string"},
                            "owner_department": {"type": "string"},
                            "purchase_date": {"type": "string"},
                        },
                    ),
                )
            },
            "/assets/{asset_id}/maintenance": {
                "get": op(
                    "getMaintenanceHistory",
                    "Retrieve the maintenance and repair history for a registered asset.",
                    params=[path_param("asset_id")],
                )
            },
            "/assets/{asset_id}/maintenance/schedule": {
                "post": op(
                    "scheduleMaintenanceEvent",
                    "Schedule a maintenance or inspection event for an asset.",
                    params=[path_param("asset_id")],
                    body_schema=schema(
                        ["scheduled_date", "maintenance_type"],
                        {"scheduled_date": {"type": "string"}, "maintenance_type": {"type": "string"}},
                    ),
                )
            },
            "/assets/{asset_id}/transfer": {
                "post": op(
                    "transferAsset",
                    "Transfer asset ownership from one department or employee to another.",
                    params=[path_param("asset_id")],
                    body_schema=schema(
                        ["new_owner_department"],
                        {"new_owner_department": {"type": "string"}, "new_owner_employee_id": {"type": "string"}},
                    ),
                )
            },
            "/assets/{asset_id}/retire": {
                "post": op(
                    "retireAsset",
                    "Retire an asset and remove it from active inventory.",
                    params=[path_param("asset_id")],
                    body_schema=schema(["retirement_reason"], {"retirement_reason": {"type": "string"}}),
                )
            },
        },
    },
}


def build_spec(domain_key: str, domain: dict) -> dict:
    return {
        "openapi": "3.0.0",
        "info": {"title": domain["title"], "version": domain["version"]},
        "security": [{"ApiKeyAuth": []}],
        "components": {"securitySchemes": {"ApiKeyAuth": SECURITY_SCHEME}},
        "paths": domain["paths"],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, domain in SPECS.items():
        spec = build_spec(key, domain)
        out_path = OUT_DIR / f"{key}.json"
        with open(out_path, "w") as f:
            json.dump(spec, f, indent=2)
        n_endpoints = sum(len(methods) for methods in domain["paths"].values())
        print(f"Wrote {out_path} ({len(domain['paths'])} paths, {n_endpoints} operations)")


if __name__ == "__main__":
    main()
