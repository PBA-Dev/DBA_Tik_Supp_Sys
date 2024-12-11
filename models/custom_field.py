import json
from db.database import Database
from psycopg2.extras import Json
from utils.audit_logger import AuditLogger
import datetime

class CustomField:
    def __init__(self):
        self.db = Database()
        self.audit_logger = AuditLogger()
        
    def delete_field(self, field_id):
        """Delete a custom field and its associated values"""
        try:
            # First delete the field values
            query1 = """
                DELETE FROM ticket_custom_fields 
                WHERE field_id = %s
            """
            self.db.execute(query1, (field_id,))
            
            # Then delete the field itself
            query2 = """
                DELETE FROM custom_fields 
                WHERE id = %s 
                RETURNING id
            """
            result = self.db.execute(query2, (field_id,))
            success = result and len(result) > 0
            if success:
                self.audit_logger.log_action(
                    operation="delete",
                    entity_type="field",
                    entity_id=field_id,
                    user_id=None,  # Will be set from the request context
                    details={"field_id": field_id}
                )
            return success
        except Exception as e:
            print(f"Error deleting field: {str(e)}")
            raise

    def create_field(self, field_name, field_type, field_options=None, is_required=False, validation_rules=None, help_text=None, depends_on=None, user_id=None):
        query = """
            INSERT INTO custom_fields (
                field_name, field_type, field_options, is_required, 
                validation_rules, help_text, depends_on
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id, field_name, field_type
        """
        # Convert dictionaries to JSON objects for PostgreSQL
        validation_rules_json = Json(validation_rules) if validation_rules else None
        depends_on_json = Json(depends_on) if depends_on else None
        
        result = self.db.execute(query, (
            field_name, field_type, field_options, is_required,
            validation_rules_json, help_text, depends_on_json
        ))
        
        if result:
            new_field = result[0]
            self.audit_logger.log_action(
                operation="create",
                entity_type="field",
                entity_id=new_field['id'],
                user_id=user_id,
                details={
                    "field_name": field_name,
                    "field_type": field_type,
                    "is_required": is_required,
                    "field_options": field_options,
                    "created_at": datetime.datetime.now().isoformat()
                }
            )
        return result

    def get_all_fields(self):
        query = """
            SELECT id, field_name, field_type, field_options, is_required,
                   validation_rules::json as validation_rules,
                   help_text,
                   depends_on::json as depends_on
            FROM custom_fields
            ORDER BY field_name
        """
        return self.db.execute(query)

    def get_field_by_id(self, field_id):
        query = """
            SELECT * FROM custom_fields
            WHERE id = %s
        """
        result = self.db.execute(query, (field_id,))
        return result[0] if result else None

    def update_field(self, field_id, field_name=None, field_type=None, field_options=None, is_required=None, user_id=None):
        # Get the original field data for audit logging
        original_field = self.get_field_by_id(field_id)
        if not original_field:
            return None

        updates = []
        params = []
        changes = {}
        
        if field_name is not None and field_name != original_field['field_name']:
            updates.append("field_name = %s")
            params.append(field_name)
            changes['field_name'] = {'old': original_field['field_name'], 'new': field_name}
            
        if field_type is not None and field_type != original_field['field_type']:
            updates.append("field_type = %s")
            params.append(field_type)
            changes['field_type'] = {'old': original_field['field_type'], 'new': field_type}
            
        if field_options is not None and field_options != original_field['field_options']:
            updates.append("field_options = %s")
            params.append(field_options)
            changes['field_options'] = {'old': original_field['field_options'], 'new': field_options}
            
        if is_required is not None and is_required != original_field['is_required']:
            updates.append("is_required = %s")
            params.append(is_required)
            changes['is_required'] = {'old': original_field['is_required'], 'new': is_required}
            
        if not updates:
            return original_field
            
        params.append(field_id)
        
        query = f"""
            UPDATE custom_fields 
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING *
        """
        result = self.db.execute(query, tuple(params))
        
        if result and result[0]:
            self.audit_logger.log_action(
                operation="update",
                entity_type="field",
                entity_id=field_id,
                user_id=user_id,
                details={
                    'changes': changes,
                    'updated_at': datetime.datetime.now().isoformat()
                }
            )
            
        return result[0] if result else None

    def save_field_value(self, ticket_id, field_id, field_value):
        query = """
            INSERT INTO ticket_custom_fields (ticket_id, field_id, field_value)
            VALUES (%s, %s, %s)
            ON CONFLICT (ticket_id, field_id) 
            DO UPDATE SET field_value = EXCLUDED.field_value
            RETURNING id
        """
        return self.db.execute(query, (ticket_id, field_id, field_value))

    def get_ticket_field_values(self, ticket_id):
        query = """
            SELECT cf.field_name, cf.field_type, tcf.field_value
            FROM ticket_custom_fields tcf
            JOIN custom_fields cf ON tcf.field_id = cf.id
            WHERE tcf.ticket_id = %s
        """
        return self.db.execute(query, (ticket_id,))
