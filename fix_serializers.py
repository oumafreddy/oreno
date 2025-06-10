from rest_framework import serializers

# Fix ProcedureSerializer
def fix_procedure_serializer():
    line = None
    with open("apps/audit/serializers.py", "r") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if "class ProcedureSerializer(BaseAuditSerializer):" in line:
            method_start = i
        if method_start and "def get_get_absolute_url(self, obj):" in line:
            # Add get_results method before get_get_absolute_url
            get_results_method = """    def get_results(self, obj):
        # Use local import to avoid circular references
        from .models.procedureresult import ProcedureResult
        results = ProcedureResult.objects.filter(procedure=obj)
        # Return basic data without using ProcedureResultSerializer
        return [{
            "id": r.id,
            "status": getattr(r, "status", None),
            "result": getattr(r, "result", None),
            "performed_date": getattr(r, "performed_date", None).isoformat() if getattr(r, "performed_date", None) else None
        } for r in results]
        
"""
            lines.insert(i, get_results_method)
            break
            
    # Fix ProcedureResultDetailSerializer
    for i, line in enumerate(lines):
        if "class ProcedureResultDetailSerializer(ProcedureResultSerializer):" in line:
            result_start = i
        if result_start and "class Meta(ProcedureResultSerializer.Meta):" in line:
            # Add get_procedure method before Meta class
            get_procedure_method = """    def get_procedure(self, obj):
        # Use local import to avoid circular references
        if obj.procedure:
            return {
                "id": obj.procedure.id,
                "title": obj.procedure.title,
                "description": getattr(obj.procedure, "description", ""),
                "procedure_type": getattr(obj.procedure, "procedure_type", "")
            }
        return None
        
"""
            lines.insert(i, get_procedure_method)
            break
    
    with open("apps/audit/serializers.py", "w") as f:
        f.writelines(lines)
    
    print("Fixed circular references in ProcedureSerializer and ProcedureResultDetailSerializer")

# Execute the fix
fix_procedure_serializer()
