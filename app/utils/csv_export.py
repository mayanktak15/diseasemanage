import csv

from ..models import User


def export_users_to_csv() -> None:
    users = User.query.all()
    with open('users.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'name', 'phone', 'email']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for user in users:
            writer.writerow({
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'email': user.email,
            })
