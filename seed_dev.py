"""Quick seed for local smoke testing.

Usage (from repo root, with venv active):
    venv/bin/python manage.py shell < seed_dev.py
or
    venv/bin/python seed_dev.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "korjo_soft.settings")
django.setup()

from organization.models import Organization, Branch, Team, User
from peoples.models import Member
from journal.models import Ledger, LedgerType
from transaction.models import TransactionCategory


def run():
    # Ledger types and ledgers (minimum needed by JournalManager)
    types = {
        "AS": "Assets",
        "LP": "Liabilities Personal",
        "AR": "Account Receivable",
        "INC": "Income",
        "EXP": "Expense",
    }
    type_objs = {}
    for code, name in types.items():
        obj, _ = LedgerType.objects.get_or_create(code=code, defaults={"name": name})
        type_objs[code] = obj

    ledgers = [
        ("CA", "Cash", "AS"),
        ("DE", "Deposit", "LP"),
        ("WI", "Withdraw", "LP"),
        ("LO", "Loan Receivable", "AR"),
        ("IN", "Installment", "AR"),
        ("INC", "Income", "INC"),
        ("EXP", "Expense", "EXP"),
    ]
    for code, name, type_code in ledgers:
        Ledger.objects.get_or_create(
            code=code,
            defaults={"name": name, "ledger_type": type_objs[type_code]},
        )

    org, _ = Organization.objects.get_or_create(name="আন-নূর কর্জে হাসানা", defaults={"code": 1001})
    branch, _ = Branch.objects.get_or_create(
        organization=org, code=1, defaults={"name": "প্রধান শাখা"}
    )

    if not User.objects.filter(username="rahim").exists():
        u = User(username="rahim", role=User.BRANCH_OWNER, branch=branch, is_active=True)
        u.set_password("password")
        u.save()

    # A handful of teams + members
    team_seed = [("জবা", 5), ("গোলাপ", 3)]
    for name, count in team_seed:
        team, _ = Team.objects.get_or_create(name=name, branch=branch)
        for i in range(1, count + 1):
            Member.objects.get_or_create(
                team=team,
                serial_number=i,
                is_active=True,
                defaults={
                    "name": f"সদস্য {name} {i}",
                    "guardian_name": f"পিতা {i}",
                    "branch": branch,
                },
            )

    # Categories
    cats = [
        ("ভর্তি ফি", "income"),
        ("দান", "income"),
        ("অফিস ভাড়া", "expense"),
        ("বিদ্যুৎ বিল", "expense"),
    ]
    for name, kind in cats:
        TransactionCategory.objects.get_or_create(name=name, category_type=kind)

    print("Seeded:")
    print("  organization:", org)
    print("  branch:", branch)
    print("  user: rahim / password")
    print("  teams:", Team.objects.count())
    print("  members:", Member.objects.count())
    print("  categories:", TransactionCategory.objects.count())


if __name__ == "__main__":
    run()
