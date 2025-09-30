from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from llm_parser import llm_parse_to_action as parse_nl_to_action, CONVERSATION_HISTORY
from pending_manager import PendingManager
from db import init_databases, query_db, execute_db, get_connection
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="NL-CRUD FastAPI - Mock Multi-DB Example")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


FRONTEND_DIR = 'frontend'

init_databases()
pending = PendingManager()

class NLRequest(BaseModel):
    text: str
    target_db: str = "hr"  

class ConfirmRequest(BaseModel):
    pending_id: int
    approve: bool

class AdvancedTestRequest(BaseModel):
    text: str
    target_db: str = "hr"
    show_metadata: bool = True

class ConversationTestRequest(BaseModel):
    queries: List[str]
    target_db: str = "hr"

@app.get('/health')
def health():
    return {"status":"ok"}

@app.post('/nl-query')
def nl_query(req: NLRequest):
    parsed = parse_nl_to_action(req.text, req.target_db)
    op = parsed.get('operation')
    
    # Enhanced response with metadata
    base_response = {
        "status": "ok",
        "operation": op,
        "sql": parsed.get('sql'),
        "table": parsed.get('table'),
        "target_db": parsed.get('target_db'),
        "metadata": {
            "business_hints": parsed.get('metadata', {}).get('business_hints', []),
            "conversation_context": parsed.get('metadata', {}).get('conversation_context', False),
            "joins": parsed.get('metadata', {}).get('joins', []),
            "group_by": parsed.get('metadata', {}).get('group_by', ''),
            "order_by": parsed.get('metadata', {}).get('order_by', ''),
            "limit": parsed.get('metadata', {}).get('limit'),
            "hitl_required": op in ('CREATE', 'UPDATE', 'DELETE')
        }
    }
    
    # HITL Logic: READ operations execute directly, CUD operations require approval
    if op == 'READ':
        sql = parsed.get('sql')
        try:
            rows = query_db(req.target_db, sql)
            base_response["result"] = rows
            base_response["execution_status"] = "executed_directly"
            return base_response
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif op in ('CREATE','UPDATE','DELETE'):
        sql = parsed.get('sql')
        # Add to pending for human approval (HITL)
        pid = pending.add_pending(req.target_db, op, sql, {
            "text": req.text,
            "metadata": parsed.get('metadata', {}),
            "table": parsed.get('table')
        })
        base_response["status"] = "pending_approval"
        base_response["pending_id"] = pid
        base_response["execution_status"] = "requires_human_approval"
        base_response["message"] = f"{op} operation requires human approval. Use /confirm endpoint to approve or reject."
        return base_response
    else:
        error_detail = "Could not interpret the query. Try a simpler phrasing."
        if parsed.get('metadata', {}).get('suggestions'):
            error_detail += f" Suggestions: {', '.join(parsed['metadata']['suggestions'])}"
        raise HTTPException(status_code=400, detail=error_detail)

@app.get('/pending')
def list_pending(status: str = 'PENDING'):
    print("Pending request called. Status filter:", status)
    return {"pending": pending.list_pending(status)}

@app.get('/pending/{pid}')
def get_pending(pid: int):
    item = pending.get(pid)
    print("Get pending item:", item)
    
    if not item:
        
        raise HTTPException(status_code=404, detail="Pending not found")
    
    return item

@app.post('/confirm')
def confirm(req: ConfirmRequest):
    item = pending.get(req.pending_id)
    print("Confirming pending item:", item)
    if not item:
        raise HTTPException(status_code=404, detail="Pending not found")
    if item['status'] != 'PENDING':
        return {"status":"noop","message":"Already processed","item":item}
    print("Confirm request:", req)
    if req.approve:
        # execute SQL
        try:
            from db import execute_db
            execute_db(item['target_db'], item['sql'])
            pending.set_status(req.pending_id, 'APPROVED')
            print("Operation approved and executed.")
            return {"status":"approved","id": req.pending_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        pending.set_status(req.pending_id, 'REJECTED')
        return {"status":"rejected","id": req.pending_id}

# ===== NEW ENHANCED TESTING ENDPOINTS =====

# @app.post('/test/advanced')
# def test_advanced_features(req: AdvancedTestRequest):
#     """Test advanced LLM parser features with full metadata"""
#     try:
#         result = parse_nl_to_action(req.text, req.target_db)
        
#         response = {
#             "status": "success",
#             "operation": result.get("operation"),
#             "table": result.get("table"),
#             "sql": result.get("sql"),
#             "target_db": result.get("target_db")
#         }
        
#         if req.show_metadata:
#             metadata = result.get("metadata", {})
#             response["metadata"] = {
#                 "business_hints": metadata.get("business_hints", []),
#                 "conversation_context": metadata.get("conversation_context", False),
#                 "joins": metadata.get("joins", []),
#                 "group_by": metadata.get("group_by", ""),
#                 "order_by": metadata.get("order_by", ""),
#                 "limit": metadata.get("limit"),
#                 "error": metadata.get("error"),
#                 "suggestions": metadata.get("suggestions", [])
#             }
        
#         return response
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"LLM Parser Error: {str(e)}")

@app.post('/test/conversation')
def test_conversation_memory(req: ConversationTestRequest):
    """Test conversation memory and context awareness"""
    results = []
    
    for i, query in enumerate(req.queries):
        try:
            result = parse_nl_to_action(query, req.target_db)
            results.append({
                "query_number": i + 1,
                "query": query,
                "operation": result.get("operation"),
                "table": result.get("table"),
                "sql": result.get("sql"),
                "conversation_context": result.get("metadata", {}).get("conversation_context", False),
                "business_hints": result.get("metadata", {}).get("business_hints", [])
            })
        except Exception as e:
            results.append({
                "query_number": i + 1,
                "query": query,
                "error": str(e)
            })
    
    return {
        "status": "success",
        "total_queries": len(req.queries),
        "results": results
    }

@app.get('/test/conversation-history')
def get_conversation_history():
    """Get current conversation history"""
    return {
        "status": "success",
        "history_length": len(CONVERSATION_HISTORY),
        "history": CONVERSATION_HISTORY[-10:]  # Last 10 queries
    }

@app.post('/test/clear-conversation')
def clear_conversation():
    """Clear conversation history"""
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY.clear()
    return {"status": "success", "message": "Conversation history cleared"}

@app.get('/test/schema/{target_db}')
def get_enhanced_schema(target_db: str):
    """Get enhanced schema information for a database"""
    from llm_parser import SCHEMA
    
    if target_db not in SCHEMA:
        raise HTTPException(status_code=404, detail=f"Database '{target_db}' not found")
    
    return {
        "status": "success",
        "target_db": target_db,
        "schema": SCHEMA[target_db]
    }


# ===== NEW DATABASE MANAGEMENT ENDPOINTS =====

@app.get('/databases')
def list_databases():
    """List all available databases"""
    from db import DB_MAP
    databases = []
    for db_name, db_path in DB_MAP.items():
        databases.append({
            "name": db_name,
            "path": db_path,
            "status": "available"
        })
    return {
        "status": "success",
        "databases": databases,
        "total": len(databases)
    }

@app.get('/databases/{db_name}/info')
def get_database_info(db_name: str):
    """Get detailed information about a specific database"""
    from db import DB_MAP, get_connection
    from llm_parser import SCHEMA
    
    if db_name not in DB_MAP:
        raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")
    
    try:
        conn = get_connection(db_name)
        cursor = conn.cursor()
        
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get row counts for each table
        table_stats = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_stats[table] = count
        
        conn.close()
        
        # Get schema information
        schema_info = SCHEMA.get(db_name, {})
        
        return {
            "status": "success",
            "database": db_name,
            "tables": tables,
            "table_stats": table_stats,
            "schema": schema_info,
            "total_tables": len(tables),
            "total_records": sum(table_stats.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing database: {str(e)}")

@app.post('/databases/init')
def initialize_databases():
    """Initialize all databases with fresh data"""
    try:
        from init_db import init_hr, init_healthcare, init_ecommerce, init_finance, init_education

        # Initialize all databases
        init_hr()
        init_healthcare()
        init_ecommerce()
        init_finance()
        init_education()
        
        return {
            "status": "success",
            "message": "All databases initialized successfully",
            "databases": ["hr", "healthcare", "ecommerce", "finance", "education"]
        }
        
    except Exception as e:
        print("eoor ",str(e))
        raise HTTPException(status_code=500, detail=f"Error initializing databases: {str(e)}")

# ===== ENHANCED HITL ENDPOINTS =====

@app.get('/pending/{pid}/details')
def get_pending_details(pid: int):
    """Get detailed information about a pending operation"""
    item = pending.get(pid)
    if not item:
        raise HTTPException(status_code=404, detail="Pending operation not found")
    
    # Enhance with additional context
    enhanced_item = dict(item)
    enhanced_item["risk_assessment"] = _assess_operation_risk(item)
    enhanced_item["affected_tables"] = _extract_affected_tables(item.get('sql', ''))
    
    return {
        "status": "success",
        "pending_operation": enhanced_item
    }

@app.post('/pending/{pid}/approve-with-modifications')
def approve_with_modifications(pid: int, modified_sql: str):
    """Approve a pending operation but with SQL modifications"""
    item = pending.get(pid)
    if not item:
        raise HTTPException(status_code=404, detail="Pending operation not found")
    
    if item['status'] != 'PENDING':
        return {"status": "noop", "message": "Already processed", "item": item}
    
    try:
        # Execute the modified SQL
        from db import execute_db
        execute_db(item['target_db'], modified_sql)
        pending.set_status(pid, 'APPROVED')
        
        return {
            "status": "approved_with_modifications",
            "id": pid,
            "original_sql": item['sql'],
            "modified_sql": modified_sql,
            "message": "Operation approved and executed with modifications"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error executing modified SQL: {str(e)}")

@app.get('/hitl/stats')
def get_hitl_statistics():
    """Get HITL statistics and performance metrics"""
    all_pending = pending.list_pending()
    
    stats = {
        "total_operations": len(all_pending),
        "pending_operations": len([p for p in all_pending if p['status'] == 'PENDING']),
        "approved_operations": len([p for p in all_pending if p['status'] == 'APPROVED']),
        "rejected_operations": len([p for p in all_pending if p['status'] == 'REJECTED']),
        "operations_by_type": {},
        "operations_by_database": {},
        "recent_operations": all_pending[-10:] if all_pending else []
    }
    
    # Count by operation type
    for op in all_pending:
        op_type = op.get('operation', 'UNKNOWN')
        stats["operations_by_type"][op_type] = stats["operations_by_type"].get(op_type, 0) + 1
        
        db = op.get('target_db', 'unknown')
        stats["operations_by_database"][db] = stats["operations_by_database"].get(db, 0) + 1
    
    return {
        "status": "success",
        "hitl_statistics": stats
    }

# ===== HELPER FUNCTIONS =====

def _assess_operation_risk(item: dict) -> dict:
    """Assess the risk level of a database operation"""
    sql = item.get('sql', '').lower()
    operation = item.get('operation', '')
    target_db = item.get('target_db', '')
    
    risk_level = "LOW"
    risk_factors = []
    
    if operation == 'DELETE':
        risk_level = "HIGH"
        risk_factors.append("DELETE operation - data will be permanently removed")
    
    if 'where' not in sql and operation in ['UPDATE', 'DELETE']:
        risk_level = "CRITICAL"
        risk_factors.append("No WHERE clause - affects all rows")
    
    if 'drop' in sql or 'truncate' in sql:
        risk_level = "CRITICAL"
        risk_factors.append("Table structure modification")
    
    if target_db == 'finance':
        risk_factors.append("Financial data - high sensitivity")
        if risk_level == "LOW":
            risk_level = "MEDIUM"
    
    if target_db == 'healthcare':
        risk_factors.append("Healthcare data - HIPAA compliance required")
        if risk_level == "LOW":
            risk_level = "MEDIUM"
    
    return {
        "level": risk_level,
        "factors": risk_factors,
        "recommendation": _get_risk_recommendation(risk_level)
    }

def _extract_affected_tables(sql: str) -> list:
    """Extract table names from SQL statement"""
    import re
    # Simple regex to find table names in SQL
    table_pattern = r'(?:FROM|JOIN|UPDATE|INSERT INTO|DELETE FROM)\s+(\w+)'
    tables = re.findall(table_pattern, sql, re.IGNORECASE)
    return list(set(tables))  # Remove duplicates

def _get_risk_recommendation(risk_level: str) -> str:
    """Get recommendation based on risk level"""
    recommendations = {
        "LOW": "Operation appears safe to approve",
        "MEDIUM": "Review operation carefully before approval",
        "HIGH": "Requires thorough review and confirmation",
        "CRITICAL": "DO NOT APPROVE without extensive review and backup"
    }
    return recommendations.get(risk_level, "Unknown risk level")

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")