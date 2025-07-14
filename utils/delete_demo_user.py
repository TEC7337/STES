from db.connection import get_database_manager

def delete_demo_user():
    db = get_database_manager()
    with db.get_session() as session:
        from models.database import Employee
        emp = session.query(Employee).filter_by(email='demo.user@example.com').first()
        if emp:
            session.delete(emp)
            print('Deleted old Demo User.')
        else:
            print('No Demo User found to delete.')

if __name__ == "__main__":
    delete_demo_user() 