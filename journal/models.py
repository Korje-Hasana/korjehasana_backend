from django.db import models
from .managers import JournalManager


class LedgerType(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Ledger(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    ledger_type = models.ForeignKey(LedgerType, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class GeneralJournal(models.Model):
    date = models.DateField()
    accounts = models.ForeignKey(Ledger, on_delete=models.RESTRICT)
    member = models.ForeignKey('peoples.Member', on_delete=models.SET_NULL, blank=True, null=True)
    branch = models.ForeignKey('organization.Branch', on_delete=models.RESTRICT)
    debit = models.IntegerField(default=0)
    credit = models.IntegerField(default=0)
    remarks = models.CharField(max_length=250, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = JournalManager()

    # class Meta:
    #     unique_together = ('date', 'accounts', 'member')
