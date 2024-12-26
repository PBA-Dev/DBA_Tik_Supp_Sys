## Database Configuration

### Required Environment Variable
You MUST set the `DATABASE_URL` environment variable before running the application. 

#### For Windows (Command Prompt):
```
set DATABASE_URL=postgresql://username:password@localhost:5432/your_database_name
```

#### For Windows (PowerShell):
```
$env:DATABASE_URL='postgresql://username:password@localhost:5432/your_database_name'
```

#### For Unix/Mac:
```
export DATABASE_URL='postgresql://username:password@localhost:5432/your_database_name'
```

### Connection String Components
- `username`: Your PostgreSQL username
- `password`: Your PostgreSQL password
- `localhost`: Database host (can be localhost or remote server)
- `5432`: Default PostgreSQL port
- `your_database_name`: Name of your database

### Prerequisites
1. PostgreSQL installed
2. Database created
3. User with appropriate permissions
