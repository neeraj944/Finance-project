import random
from datetime import date, timedelta
from django.contrib.auth.models import User
from forecast_app.models import Receivable, Payable

user = User.objects.get(username="admin11")
today = date.today()

party_names = [
    "ABC Solutions", "Apex Global", "Vertex Solutions", "Fusion Systems",
    "Alpha Innovations", "Skyline Corp", "BrightWave Labs",
    "NextGen Softwares", "BluePeak Systems", "Quantum Services",
    "Nimbus Technologies", "Orion Tech", "Nova Enterprises"
]

receivables = []
payables = []

# ---------- RECEIVABLES ----------
for i in range(500):
    is_received = random.choice([True, False])

    receivables.append(
        Receivable(
            user=user,
            party_name=random.choice(party_names),
            amount=random.randint(5000, 100000),
            due_date=today + timedelta(days=random.randint(-180, 180)),
            description=None,
            is_received=is_received,
            received_date=(
                today - timedelta(days=random.randint(0, 30))
                if is_received else None
            ),
        )
    )

# ---------- PAYABLES ----------
for i in range(500):
    is_paid = random.choice([True, False])

    payables.append(
        Payable(
            user=user,
            party_name=random.choice(party_names),
            amount=random.randint(5000, 100000),
            due_date=today + timedelta(days=random.randint(-180, 180)),
            description=None,
            is_paid=is_paid,
            paid_date=(
                today - timedelta(days=random.randint(0, 30))
                if is_paid else None
            ),
        )
    )

Receivable.objects.bulk_create(receivables)
Payable.objects.bulk_create(payables)

print("✅ 500 Receivables created")
print("✅ 500 Payables created")
