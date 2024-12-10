from db.database import Database

class CustomField:
    def __init__(self):
        self.db = Database()

    def create_field(self, field_name, field_type, field_options=None, is_required=False, validation_rules=None, help_text=None, depends_on=None):
        query = """
            INSERT INTO custom_fields (
                field_name, field_type, field_options, is_required, 
                validation_rules, help_text, depends_on
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        return self.db.execute(query, (
            field_name, field_type, field_options, is_required,
            validation_rules, help_text, depends_on
        ))

    def get_all_fields(self):
        query = """
            SELECT * FROM custom_fields
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

    def update_field(self, field_id, field_name=None, field_type=None, field_options=None, is_required=None):
        updates = []
        params = []
        
        if field_name is not None:
            updates.append("field_name = %s")
            params.append(field_name)
        if field_type is not None:
            updates.append("field_type = %s")
            params.append(field_type)
        if field_options is not None:
            updates.append("field_options = %s")
            params.append(field_options)
        if is_required is not None:
            updates.append("is_required = %s")
            params.append(is_required)
            
        if not updates:
            return None
            
        params.append(field_id)
        
        query = f"""
            UPDATE custom_fields 
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING *
        """
        result = self.db.execute(query, tuple(params))
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
