def execute_sql_file(self, cursor, filename):
    """Execute SQL commands from a file with error handling"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            sql_commands = file.read().split(';')
            
            for command in sql_commands:
                command = command.strip()
                if command and not command.startswith('--'):
                    try:
                        cursor.execute(command)
                        print(f"✅ Executed: {command[:50]}..." if len(command) > 50 else f"✅ Executed: {command}")
                    except Error as e:
                        if 'Duplicate key name' in str(e):
                            print(f"⚠️  Index already exists: {command[:50]}...")
                        else:
                            print(f"❌ Error in command: {e}")
                            # Continue with next command
        return True
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return False